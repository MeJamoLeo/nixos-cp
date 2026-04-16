#!/usr/bin/env python3
"""Fetch AtCoder stats and write JSON for the CP dashboard.

Data sources:
  1. atcoder.jp /users/{user}/history/json — rating history (official, no auth)
  2. atcoder.jp /contests/?lang=ja — upcoming contests (HTML scraping)
  3. kenkoooo.com AtCoder Problems API — submissions, difficulties (may 403)
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

JST = timezone(timedelta(hours=9))

KENKOOOO_BASE = "https://kenkoooo.com/atcoder"
ATCODER_BASE = "https://atcoder.jp"

RATING_LABELS: list[tuple[int, str]] = [
    (2800, "赤"),
    (2400, "橙"),
    (2000, "黄"),
    (1600, "青"),
    (1200, "水色"),
    (800, "緑"),
    (400, "茶色"),
    (0, "灰"),
]

# Cache TTL in seconds
TTL_RATINGS = 3600  # 1h
TTL_SUBMISSIONS = 0  # incremental
TTL_DIFFICULTIES = 86400  # 24h
TTL_PROBLEMS = 86400  # 24h
TTL_CONTESTS = 21600  # 6h


@dataclass(frozen=True)
class Config:
    username: str
    cache_dir: Path
    output_path: Path


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def _cache_path(cache_dir: Path, key: str) -> Path:
    return cache_dir / f"{key}.json"


def _meta_path(cache_dir: Path, key: str) -> Path:
    return cache_dir / f"{key}.meta.json"


def read_cache(cache_dir: Path, key: str, ttl: int) -> Any | None:
    path = _cache_path(cache_dir, key)
    meta = _meta_path(cache_dir, key)
    if not path.exists() or not meta.exists():
        return None
    try:
        m = json.loads(meta.read_text())
        if time.time() - m.get("fetched_at", 0) > ttl:
            return None
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        path.unlink(missing_ok=True)
        meta.unlink(missing_ok=True)
        return None


def read_cache_raw(cache_dir: Path, key: str) -> Any | None:
    """Read cache ignoring TTL (stale fallback)."""
    path = _cache_path(cache_dir, key)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def write_cache(cache_dir: Path, key: str, data: Any) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    _cache_path(cache_dir, key).write_text(
        json.dumps(data, ensure_ascii=False)
    )
    _meta_path(cache_dir, key).write_text(
        json.dumps({"fetched_at": time.time()})
    )


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def _fetch(url: str, retries: int = 1) -> bytes | None:
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (X11; Linux x86_64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": "application/json, text/html, */*",
                    "Accept-Encoding": "gzip",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    data = gzip.decompress(data)
                return data
        except (urllib.error.URLError, OSError) as e:
            if attempt < retries:
                time.sleep(3)
                continue
            print(f"[fetch_stats] ERROR {url}: {e}", file=sys.stderr)
            return None


def _fetch_json(url: str, retries: int = 1) -> Any | None:
    raw = _fetch(url, retries)
    if raw is None:
        return None
    try:
        return json.loads(raw.decode())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"[fetch_stats] JSON parse error {url}: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Data fetchers
# ---------------------------------------------------------------------------

def fetch_rating_history(cfg: Config) -> list[dict]:
    """Fetch from official AtCoder API."""
    cache_key = f"ratings_{cfg.username}"
    cached = read_cache(cfg.cache_dir, cache_key, TTL_RATINGS)
    if cached is not None:
        return cached

    url = f"{ATCODER_BASE}/users/{cfg.username}/history/json"
    data = _fetch_json(url)
    if data is None:
        return read_cache_raw(cfg.cache_dir, cache_key) or []
    write_cache(cfg.cache_dir, cache_key, data)
    return data


def fetch_submissions_kenkoooo(cfg: Config) -> list[dict]:
    """Fetch submissions via kenkoooo API (may fail with 403)."""
    cache_key = f"submissions_{cfg.username}"
    path = _cache_path(cfg.cache_dir, cache_key)

    cached: list[dict] = []
    last_epoch = 0
    if path.exists():
        try:
            cached = json.loads(path.read_text())
            if cached:
                last_epoch = max(s.get("epoch_second", 0) for s in cached) + 1
        except (json.JSONDecodeError, OSError):
            cached = []

    from_second = last_epoch
    new_subs: list[dict] = []

    while True:
        url = (
            f"{KENKOOOO_BASE}/atcoder-api/v3/user/submissions"
            f"?user={cfg.username}&from_second={from_second}"
        )
        batch = _fetch_json(url)
        if batch is None:
            break
        if isinstance(batch, dict) and "message" in batch:
            # API returned error (e.g. {"message": "Forbidden"})
            print(
                f"[fetch_stats] kenkoooo API error: {batch['message']}",
                file=sys.stderr,
            )
            break
        new_subs.extend(batch)
        if len(batch) < 500:
            break
        from_second = max(s["epoch_second"] for s in batch) + 1
        time.sleep(1)

    if new_subs:
        all_subs = cached + new_subs
        write_cache(cfg.cache_dir, cache_key, all_subs)
        return all_subs
    return cached


def fetch_difficulties_kenkoooo(cfg: Config) -> dict[str, Any]:
    cache_key = "problem_models"
    cached = read_cache(cfg.cache_dir, cache_key, TTL_DIFFICULTIES)
    if cached is not None:
        return cached

    url = f"{KENKOOOO_BASE}/resources/problem-models.json"
    data = _fetch_json(url)
    if data is None or (isinstance(data, dict) and "message" in data):
        return read_cache_raw(cfg.cache_dir, cache_key) or {}
    write_cache(cfg.cache_dir, cache_key, data)
    return data


def fetch_problems_kenkoooo(cfg: Config) -> list[dict]:
    cache_key = "problems"
    cached = read_cache(cfg.cache_dir, cache_key, TTL_PROBLEMS)
    if cached is not None:
        return cached

    url = f"{KENKOOOO_BASE}/resources/problems.json"
    data = _fetch_json(url)
    if data is None or (isinstance(data, dict) and "message" in data):
        return read_cache_raw(cfg.cache_dir, cache_key) or []
    write_cache(cfg.cache_dir, cache_key, data)
    return data


def fetch_upcoming_contests(cfg: Config) -> list[dict]:
    """Scrape upcoming contests from atcoder.jp/contests."""
    cache_key = "upcoming_contests"
    cached = read_cache(cfg.cache_dir, cache_key, TTL_CONTESTS)
    if cached is not None:
        return cached

    raw = _fetch(f"{ATCODER_BASE}/contests/?lang=ja")
    if raw is None:
        return read_cache_raw(cfg.cache_dir, cache_key) or []

    html = raw.decode("utf-8", errors="replace")
    contests = _parse_contests_html(html)
    if contests:
        write_cache(cfg.cache_dir, cache_key, contests)
    return contests


def _parse_contests_html(html: str) -> list[dict]:
    """Extract upcoming contests from the contests page HTML."""
    contests: list[dict] = []
    now = time.time()

    # Find all contest rows: <time>...</time> paired with <a href="/contests/xxx">
    # Pattern: time tag followed by contest link in the same table row
    time_pattern = re.compile(
        r"<time[^>]*>(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\+\d{4})</time>"
    )
    link_pattern = re.compile(
        r'<a href="/contests/([^"]+)">([^<]+)</a>'
    )
    rated_pattern = re.compile(
        r"(~ \d+|All)"
    )

    # Split by table rows
    rows = html.split("<tr")
    for row in rows:
        times = time_pattern.findall(row)
        links = link_pattern.findall(row)
        if not times or not links:
            continue

        # Take the first time (start) and last link (contest name)
        time_str = times[0]
        try:
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S%z")
            start_epoch = int(dt.timestamp())
        except ValueError:
            continue

        # Skip past contests
        if start_epoch < now:
            continue

        # Find contest link (skip timeanddate.com links)
        contest_id = ""
        contest_title = ""
        for cid, ctitle in links:
            if "timeanddate" not in cid:
                contest_id = cid
                contest_title = ctitle
                break
        if not contest_id:
            continue

        # Skip Daily Training and non-regular contests
        if "adt_" in contest_id or "masters" in contest_id or "awc" in contest_id:
            continue

        # Determine type
        if contest_id.startswith("abc"):
            ctype = "ABC"
            rated = "〜1999"
        elif contest_id.startswith("arc"):
            ctype = "ARC"
            rated = "〜2799"
        elif contest_id.startswith("agc"):
            ctype = "AGC"
            rated = "All"
        elif contest_id.startswith("ahc"):
            ctype = "AHC"
            rated = "All"
        else:
            ctype = "Other"
            rated = ""

        is_rated = ctype in ("ABC", "AHC")

        # Duration: look for two <time> tags (start + end)
        duration = 6000  # default 100min
        if len(times) >= 2:
            try:
                dt_end = datetime.strptime(times[1], "%Y-%m-%d %H:%M:%S%z")
                duration = int(dt_end.timestamp()) - start_epoch
            except ValueError:
                pass

        contests.append({
            "id": contest_id,
            "title": contest_title,
            "type": ctype,
            "start_epoch": start_epoch,
            "duration_seconds": duration,
            "rated_range": rated,
            "is_rated_for_user": is_rated,
        })

    contests.sort(key=lambda x: x["start_epoch"])
    return contests[:8]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rating_label(rating: int) -> str:
    for threshold, label in RATING_LABELS:
        if rating >= threshold:
            return label
    return "灰"


def _rating_band(rating: int) -> tuple[int, int]:
    for i, (threshold, _) in enumerate(RATING_LABELS):
        if rating >= threshold:
            upper = RATING_LABELS[i - 1][0] if i > 0 else 9999
            return threshold, upper
    return 0, 400


def _epoch_to_jst_date(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, tz=JST).strftime("%Y-%m-%d")


def _today_jst() -> str:
    return datetime.now(JST).strftime("%Y-%m-%d")


def _ac_problems(submissions: list[dict]) -> dict[str, dict]:
    ac_map: dict[str, dict] = {}
    for s in sorted(submissions, key=lambda x: x.get("epoch_second", 0)):
        pid = s.get("problem_id", "")
        if s.get("result") == "AC" and pid not in ac_map:
            ac_map[pid] = s
    return ac_map


def _guess_tag(problem_id: str, contest_id: str, difficulty: float) -> str:
    pid = problem_id.lower()
    cid = contest_id.lower()

    if "edpc" in cid or "dp" in pid:
        return "DP"
    if pid.endswith("_a") or pid.endswith("_b"):
        return "実装"
    if difficulty < 400:
        return "実装"
    if difficulty < 800:
        return "累積和"
    return "アルゴリズム"


def _load_tag_overrides() -> dict[str, str]:
    path = Path.home() / ".cp" / "tag_overrides.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


# ---------------------------------------------------------------------------
# Transformers
# ---------------------------------------------------------------------------

def build_hud(
    submissions: list[dict],
    ratings: list[dict],
    streak_days: int,
    max_streak: int,
) -> dict:
    ac_map = _ac_problems(submissions)
    total = len(submissions)
    wa_count = sum(1 for s in submissions if s.get("result") == "WA")
    wa_rate = wa_count / total if total > 0 else 0.0

    current_rating = ratings[-1]["NewRating"] if ratings else 0

    today = _today_jst()
    today_acs = [
        s for s in submissions
        if _epoch_to_jst_date(s.get("epoch_second", 0)) == today
        and s.get("result") == "AC"
    ]
    first_ac_today = ""
    if today_acs:
        earliest = min(today_acs, key=lambda s: s["epoch_second"])
        first_ac_today = datetime.fromtimestamp(
            earliest["epoch_second"], tz=JST
        ).strftime("%H:%M")

    # Average first AC time (last 30 days)
    thirty_days_ago = datetime.now(JST) - timedelta(days=30)
    by_date: dict[str, list[dict]] = {}
    for s in submissions:
        if s.get("result") != "AC":
            continue
        dt = datetime.fromtimestamp(s["epoch_second"], tz=JST)
        if dt >= thirty_days_ago:
            by_date.setdefault(dt.strftime("%Y-%m-%d"), []).append(s)
    daily_first_minutes: list[int] = []
    for subs in by_date.values():
        earliest = min(subs, key=lambda s: s["epoch_second"])
        dt = datetime.fromtimestamp(earliest["epoch_second"], tz=JST)
        daily_first_minutes.append(dt.hour * 60 + dt.minute)
    avg_first_ac = ""
    if daily_first_minutes:
        avg = sum(daily_first_minutes) // len(daily_first_minutes)
        avg_first_ac = f"{avg // 60}:{avg % 60:02d}"

    return {
        "rating": current_rating,
        "rank_label": _rating_label(current_rating),
        "streak_days": streak_days,
        "max_streak": max_streak,
        "ac_count": len(ac_map),
        "wa_rate": round(wa_rate, 3),
        "first_ac_today": first_ac_today,
        "avg_first_ac": avg_first_ac,
    }


def build_player_status(
    submissions: list[dict],
    ratings: list[dict],
    difficulties: dict[str, Any],
    streak_days: int,
    max_streak: int,
) -> dict:
    current_rating = ratings[-1]["NewRating"] if ratings else 0
    band_low, band_high = _rating_band(current_rating)
    progress = (
        (current_rating - band_low) / (band_high - band_low)
        if band_high > band_low
        else 0
    )

    ac_map = _ac_problems(submissions)
    level = len(ac_map) // 10

    today = _today_jst()
    today_acs: list[dict] = []
    seen: set[str] = set()
    for s in submissions:
        if s.get("result") != "AC":
            continue
        if _epoch_to_jst_date(s.get("epoch_second", 0)) != today:
            continue
        pid = s.get("problem_id", "")
        if pid in seen:
            continue
        seen.add(pid)
        diff = difficulties.get(pid, {}).get("difficulty") or 0
        if diff < 0:
            diff = 0
        today_acs.append({
            "problem_id": pid,
            "difficulty": round(diff),
            "xp": round(max(diff, 100)),
        })

    return {
        "rating": current_rating,
        "rating_min": band_low,
        "rating_max": band_high,
        "rating_progress": round(progress, 3),
        "level": level,
        "today_xp": sum(a["xp"] for a in today_acs),
        "streak_days": streak_days,
        "max_streak": max_streak,
        "today_acs": today_acs,
    }


def build_wa_queue(
    submissions: list[dict],
    difficulties: dict[str, Any],
    problems_list: list[dict],
    tag_overrides: dict[str, str],
) -> list[dict]:
    problems_map = {p["id"]: p for p in problems_list}

    by_problem: dict[str, list[dict]] = {}
    for s in submissions:
        by_problem.setdefault(s.get("problem_id", ""), []).append(s)

    queue: list[dict] = []
    for pid, subs in by_problem.items():
        has_ac = any(s.get("result") == "AC" for s in subs)
        wa_count = sum(1 for s in subs if s.get("result") == "WA")
        if wa_count > 0 and not has_ac:
            diff = difficulties.get(pid, {}).get("difficulty") or 0
            if diff < 0:
                diff = 0
            cid = problems_map.get(pid, {}).get("contest_id", "")
            tag = tag_overrides.get(pid, _guess_tag(pid, cid, diff))
            last_wa = max(
                (s["epoch_second"] for s in subs if s.get("result") == "WA"),
                default=0,
            )
            queue.append({
                "problem_id": pid,
                "wa_count": wa_count,
                "tag": tag,
                "difficulty": round(diff),
                "last_wa_epoch": last_wa,
            })

    queue.sort(key=lambda x: (-x["wa_count"], -x["difficulty"]))
    return queue[:8]


def build_difficulty_log(
    submissions: list[dict],
    difficulties: dict[str, Any],
    ratings: list[dict],
) -> dict:
    ac_map = _ac_problems(submissions)
    current_rating = ratings[-1]["NewRating"] if ratings else 0

    points: list[dict] = []
    for pid, s in ac_map.items():
        diff = difficulties.get(pid, {}).get("difficulty")
        if diff is not None and diff >= 0:
            points.append({
                "epoch": s["epoch_second"],
                "difficulty": round(diff),
            })
    points.sort(key=lambda x: x["epoch"])

    # 6ヶ月分にフィルタ
    now = time.time()
    six_months_ago = now - 180 * 86400
    recent_points = [p for p in points if p["epoch"] >= six_months_ago]

    # Weekly difficulty sums (棒グラフ用)
    weekly_diff_sums: list[dict] = []
    if recent_points:
        week_sums: dict[int, dict] = {}
        first_epoch = recent_points[0]["epoch"]
        for p in recent_points:
            wk = (p["epoch"] - first_epoch) // (7 * 86400)
            wk_epoch = first_epoch + wk * 7 * 86400
            if wk_epoch not in week_sums:
                week_sums[wk_epoch] = {
                    "epoch": wk_epoch, "sum": 0, "count": 0,
                }
            week_sums[wk_epoch]["sum"] += p["difficulty"]
            week_sums[wk_epoch]["count"] += 1
        weekly_diff_sums = sorted(
            week_sums.values(), key=lambda x: x["epoch"],
        )

    # Rating-based projections from recent contest trend
    projections: list[dict] = []
    if len(ratings) >= 3:
        recent_r = ratings[-5:]
        first_r, last_r = recent_r[0], recent_r[-1]
        first_ep = first_r.get("EndTime", 0)
        last_ep = last_r.get("EndTime", 0)
        if isinstance(first_ep, str):
            try:
                first_ep = int(
                    datetime.fromisoformat(first_ep).timestamp()
                )
            except ValueError:
                first_ep = 0
        if isinstance(last_ep, str):
            try:
                last_ep = int(
                    datetime.fromisoformat(last_ep).timestamp()
                )
            except ValueError:
                last_ep = 0
        days_span = (last_ep - first_ep) / 86400
        if days_span > 0:
            rate_per_day = (
                last_r["NewRating"] - first_r["NewRating"]
            ) / days_span
            cur_epoch = last_ep
            cur_r = last_r["NewRating"]

            for scenario, multiplier in [
                ("optimistic", 1.5),
                ("maintain", 1.0),
                ("pessimistic", 0.3),
            ]:
                proj_points = []
                for week in range(1, 14):
                    future_epoch = cur_epoch + week * 7 * 86400
                    future_r = (
                        cur_r + rate_per_day * week * 7 * multiplier
                    )
                    future_r = max(0, min(2800, future_r))
                    proj_points.append({
                        "epoch": round(future_epoch),
                        "rating": round(future_r),
                    })
                projections.append({
                    "scenario": scenario,
                    "points": proj_points,
                })

    return {
        "points": recent_points,
        "weekly_diff_sums": weekly_diff_sums,
        "current_rating": current_rating,
        "projections": projections,
    }


def build_tag_ac_rate(
    submissions: list[dict],
    problems_list: list[dict],
    difficulties: dict[str, Any],
    tag_overrides: dict[str, str],
) -> list[dict]:
    problems_map = {p["id"]: p for p in problems_list}

    # Track per-problem per-tag: was it AC'd?
    problem_results: dict[str, dict[str, bool]] = {}  # tag -> {pid: ac?}
    for s in submissions:
        pid = s.get("problem_id", "")
        cid = problems_map.get(pid, {}).get("contest_id", "")
        diff = difficulties.get(pid, {}).get("difficulty") or 0
        if diff < 0:
            diff = 0
        tag = tag_overrides.get(pid, _guess_tag(pid, cid, diff))

        if tag not in problem_results:
            problem_results[tag] = {}
        if pid not in problem_results[tag]:
            problem_results[tag][pid] = False
        if s.get("result") == "AC":
            problem_results[tag][pid] = True

    result = []
    for tag, pids in problem_results.items():
        total = len(pids)
        ac = sum(1 for v in pids.values() if v)
        if total >= 3:
            result.append({
                "tag": tag,
                "ac_rate": round(ac / total, 2) if total > 0 else 0,
                "total": total,
                "ac": ac,
            })
    result.sort(key=lambda x: -x["ac_rate"])
    return result[:8]


def build_streak_calendar(
    submissions: list[dict],
    difficulties: dict[str, Any],
) -> tuple[list[dict], int, int]:
    # Group ACs by JST date
    by_date: dict[str, set[str]] = {}
    diff_by_date: dict[str, float] = {}
    for s in submissions:
        if s.get("result") != "AC":
            continue
        d = _epoch_to_jst_date(s.get("epoch_second", 0))
        pid = s.get("problem_id", "")
        by_date.setdefault(d, set()).add(pid)
        diff = difficulties.get(pid, {}).get("difficulty") or 0
        if diff < 0:
            diff = 0
        diff_by_date[d] = max(diff_by_date.get(d, 0), diff)

    today = datetime.now(JST).date()
    calendar: list[dict] = []
    for i in range(27, -1, -1):
        d = today - timedelta(days=i)
        ds = d.isoformat()
        calendar.append({
            "date": ds,
            "max_difficulty": round(diff_by_date.get(ds, 0)),
            "ac_count": len(by_date.get(ds, set())),
        })

    # Current streak
    current_streak = 0
    check = today
    if today.isoformat() not in by_date:
        check = today - timedelta(days=1)
    while check.isoformat() in by_date:
        current_streak += 1
        check -= timedelta(days=1)

    # Max streak
    all_dates = sorted(by_date.keys())
    max_streak = 0
    run = 0
    prev = None
    for ds in all_dates:
        d = datetime.strptime(ds, "%Y-%m-%d").date()
        if prev is not None and (d - prev).days == 1:
            run += 1
        else:
            run = 1
        max_streak = max(max_streak, run)
        prev = d

    return calendar, current_streak, max_streak


def build_speed(
    submissions: list[dict],
    ratings: list[dict],
) -> list[dict]:
    """Per-contest lap times (A, B, C, ...) from rated contests only."""
    # Build contest start times from rating history
    contest_starts: dict[str, int] = {}
    contest_names: dict[str, str] = {}
    for r in ratings:
        screen = r.get("ContestScreenName", "")
        cid = screen.split(".")[0] if "." in screen else ""
        end_epoch = r.get("EndTime", 0)
        if isinstance(end_epoch, str):
            try:
                end_epoch = int(
                    datetime.fromisoformat(end_epoch).timestamp()
                )
            except ValueError:
                continue
        # ABC = 100min, ARC = 120min
        duration = 7200 if cid.startswith("arc") else 6000
        if cid:
            contest_starts[cid] = end_epoch - duration
            contest_names[cid] = r.get("ContestName", cid)

    # Group AC submissions by contest
    contest_acs: dict[str, list[dict]] = {}
    for s in submissions:
        if s.get("result") != "AC":
            continue
        cid = s.get("contest_id", "")
        if cid not in contest_starts:
            continue
        contest_acs.setdefault(cid, []).append(s)

    result = []
    for cid in sorted(contest_starts.keys(), key=lambda c: contest_starts[c]):
        start = contest_starts[cid]
        acs = contest_acs.get(cid, [])
        if not acs:
            continue

        # First AC per problem, sorted by AC time
        first_ac: dict[str, int] = {}
        for s in sorted(acs, key=lambda x: x["epoch_second"]):
            pid = s.get("problem_id", "")
            if pid not in first_ac:
                first_ac[pid] = s["epoch_second"]

        # Sort by AC time → lap order
        sorted_acs = sorted(first_ac.items(), key=lambda x: x[1])

        laps = []
        prev_time = start
        for pid, ac_time in sorted_acs:
            cumulative = ac_time - start
            lap = ac_time - prev_time
            if cumulative <= 0 or cumulative > 10800:
                continue
            # Problem label: last part after underscore (a, b, c, ...)
            label = pid.rsplit("_", 1)[-1].upper() if "_" in pid else pid
            laps.append({
                "problem": label,
                "cumulative": cumulative,
                "lap": lap,
            })
            prev_time = ac_time

        if laps:
            name = contest_names.get(cid, cid)
            short = name.replace("AtCoder Beginner Contest ", "ABC ")
            short = short.replace("AtCoder Regular Contest ", "ARC ")
            duration = 7200 if cid.startswith("arc") else 6000
            result.append({
                "contest": short,
                "start_epoch": start,
                "duration_seconds": duration,
                "laps": laps,
            })

    return result[-6:]


def build_rating_log(ratings: list[dict]) -> list[dict]:
    """Transform rating history for the difficulty log chart."""
    result = []
    for r in ratings:
        end_time = r.get("EndTime", 0)
        if isinstance(end_time, str):
            try:
                end_time = int(datetime.fromisoformat(end_time).timestamp())
            except ValueError:
                continue
        result.append({
            "epoch": end_time,
            "old_rating": r.get("OldRating", 0),
            "new_rating": r.get("NewRating", 0),
            "contest": r.get("ContestName", ""),
            "place": r.get("Place", 0),
            "performance": r.get("Performance", 0),
        })
    return result


def build_skill_graph(
    submissions: list[dict],
    difficulties: dict[str, Any],
    problems_list: list[dict],
    ratings: list[dict],
) -> dict:
    """Build skill tree with progress computed from AC data.

    Progress for each skill = number of distinct AC'd problems
    matching the skill's difficulty range and problem patterns,
    capped at a target count per skill.
    """
    current_rating = ratings[-1]["NewRating"] if ratings else 0

    # AC'd problems with their difficulty
    ac_map = _ac_problems(submissions)
    problems_map = {p["id"]: p for p in problems_list}
    ac_with_diff: list[dict] = []
    for pid, s in ac_map.items():
        diff = difficulties.get(pid, {}).get("difficulty")
        if diff is None:
            continue
        if diff < 0:
            diff = 0
        cid = problems_map.get(pid, {}).get("contest_id", "")
        ac_with_diff.append({
            "pid": pid,
            "cid": cid,
            "diff": round(diff),
        })

    # Skill definitions: difficulty range + contest/problem patterns
    # target = number of ACs to consider "mastered"
    SKILLS = {
        # Tier 1 (灰→茶): diff 0-799
        "bruteforce":  {"diff_min": 0,   "diff_max": 799,  "target": 20, "patterns": ["_a", "_b", "_c"]},
        "sort":        {"diff_min": 0,   "diff_max": 599,  "target": 15, "patterns": ["_a", "_b"]},
        "greedy":      {"diff_min": 200, "diff_max": 999,  "target": 10, "patterns": ["_c", "_d"]},
        "string":      {"diff_min": 0,   "diff_max": 799,  "target": 10, "patterns": ["_b", "_c"]},
        "mapset":      {"diff_min": 0,   "diff_max": 599,  "target": 10, "patterns": ["_b", "_c"]},
        "gcd":         {"diff_min": 100, "diff_max": 799,  "target": 8,  "patterns": ["_b", "_c"]},
        "simulation":  {"diff_min": 0,   "diff_max": 599,  "target": 20, "patterns": ["_a", "_b"]},
        # Tier 2 (茶→緑): diff 400-1199
        "cumsum":      {"diff_min": 400, "diff_max": 1199, "target": 8,  "patterns": ["_c", "_d"]},
        "binsearch":   {"diff_min": 400, "diff_max": 1199, "target": 8,  "patterns": ["_c", "_d"]},
        "basedp":      {"diff_min": 400, "diff_max": 1199, "target": 10, "patterns": ["_c", "_d", "_e"], "contest_patterns": ["edpc", "dp"]},
        "bfs":         {"diff_min": 400, "diff_max": 1199, "target": 8,  "patterns": ["_c", "_d", "_e"]},
        "twoptr":      {"diff_min": 600, "diff_max": 1199, "target": 5,  "patterns": ["_d", "_e"]},
        "bit":         {"diff_min": 400, "diff_max": 1199, "target": 5,  "patterns": ["_c", "_d"]},
        "prime":       {"diff_min": 400, "diff_max": 1199, "target": 5,  "patterns": ["_c", "_d"]},
        "complexity":  {"diff_min": 400, "diff_max": 999,  "target": 10, "patterns": ["_c", "_d"]},
        # Tier 3 (緑→水): diff 800-1599
        "unionfind":   {"diff_min": 800, "diff_max": 1599, "target": 5,  "patterns": ["_d", "_e"]},
        "dijkstra":    {"diff_min": 800, "diff_max": 1599, "target": 5,  "patterns": ["_d", "_e"]},
        "segtree":     {"diff_min": 800, "diff_max": 1599, "target": 5,  "patterns": ["_d", "_e", "_f"]},
        "bitdp":       {"diff_min": 800, "diff_max": 1599, "target": 5,  "patterns": ["_e", "_f"]},
        "mst":         {"diff_min": 800, "diff_max": 1599, "target": 3,  "patterns": ["_d", "_e"]},
        "compress":    {"diff_min": 800, "diff_max": 1599, "target": 3,  "patterns": ["_d", "_e"]},
        "modinv":      {"diff_min": 800, "diff_max": 1599, "target": 3,  "patterns": ["_d", "_e"]},
        "imos":        {"diff_min": 600, "diff_max": 1399, "target": 3,  "patterns": ["_d", "_e"]},
    }

    # Count matching ACs per skill
    skill_counts: dict[str, int] = {}
    for skill_id, spec in SKILLS.items():
        count = 0
        for ac in ac_with_diff:
            if ac["diff"] < spec["diff_min"] or ac["diff"] > spec["diff_max"]:
                continue
            pid_lower = ac["pid"].lower()
            cid_lower = ac["cid"].lower()
            # Check problem suffix pattern
            pattern_match = any(pid_lower.endswith(p) for p in spec["patterns"])
            # Check contest pattern (optional)
            contest_match = True
            if "contest_patterns" in spec:
                contest_match = any(cp in cid_lower or cp in pid_lower for cp in spec["contest_patterns"])
                # For DP skill, also count if pattern matches even without contest pattern
                if not contest_match:
                    pattern_match = False
            if pattern_match:
                count += 1
        skill_counts[skill_id] = count

    # Build nodes with real progress
    TREE = [
        {"id": "base",       "label": "基礎",       "tier": 0, "parent": None},
        {"id": "bruteforce", "label": "全探索",     "tier": 1, "parent": "base"},
        {"id": "sort",       "label": "ソート",     "tier": 1, "parent": "base"},
        {"id": "greedy",     "label": "貪欲法",     "tier": 1, "parent": "base"},
        {"id": "string",     "label": "文字列",     "tier": 1, "parent": "base"},
        {"id": "mapset",     "label": "Map/Set",    "tier": 1, "parent": "base"},
        {"id": "gcd",        "label": "GCD/LCM",    "tier": 1, "parent": "base"},
        {"id": "simulation", "label": "実装力",     "tier": 1, "parent": "base"},
        {"id": "cumsum",     "label": "累積和",     "tier": 2, "parent": "bruteforce"},
        {"id": "binsearch",  "label": "二分探索",   "tier": 2, "parent": "sort"},
        {"id": "basedp",     "label": "基礎DP",     "tier": 2, "parent": "bruteforce"},
        {"id": "bfs",        "label": "BFS/DFS",    "tier": 2, "parent": "bruteforce"},
        {"id": "twoptr",     "label": "尺取り法",   "tier": 2, "parent": "sort"},
        {"id": "bit",        "label": "ビット演算", "tier": 2, "parent": "bruteforce"},
        {"id": "prime",      "label": "素数/約数",  "tier": 2, "parent": "gcd"},
        {"id": "complexity", "label": "計算量",     "tier": 2, "parent": "sort"},
        {"id": "unionfind",  "label": "Union-Find", "tier": 3, "parent": "bfs"},
        {"id": "dijkstra",   "label": "最短路",     "tier": 3, "parent": "bfs"},
        {"id": "segtree",    "label": "セグ木/BIT", "tier": 3, "parent": "cumsum"},
        {"id": "bitdp",      "label": "bitDP",      "tier": 3, "parent": "bit"},
        {"id": "mst",        "label": "MST",        "tier": 3, "parent": "bfs"},
        {"id": "compress",   "label": "座標圧縮",   "tier": 3, "parent": "binsearch"},
        {"id": "modinv",     "label": "mod逆元",    "tier": 3, "parent": "prime"},
        {"id": "imos",       "label": "imos法",      "tier": 3, "parent": "cumsum"},
    ]

    nodes = []
    for n in TREE:
        sid = n["id"]
        if sid == "base":
            # Base is always complete if user has any ACs
            progress = [len(ac_map), len(ac_map)] if ac_map else [0, 1]
        else:
            target = SKILLS.get(sid, {}).get("target", 5)
            count = min(skill_counts.get(sid, 0), target)
            progress = [count, target]
        node = {"id": sid, "label": n["label"], "tier": n["tier"], "progress": progress}
        if n["parent"]:
            node["parent"] = n["parent"]
        nodes.append(node)

    return {
        "rating": current_rating,
        "nodes": nodes,
        "tiers": [
            {"tier": 0, "label": "基礎", "color": "#808080"},
            {"tier": 1, "label": "灰→茶", "color": "#804000"},
            {"tier": 2, "label": "茶→緑", "color": "#008000"},
            {"tier": 3, "label": "緑→水", "color": "#00C0C0"},
        ],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch AtCoder stats")
    parser.add_argument("--user", default="MeJamoLeo")
    parser.add_argument(
        "--output",
        default=str(Path.home() / ".cache" / "cp-dashboard" / "stats.json"),
    )
    parser.add_argument(
        "--cache-dir",
        default=str(Path.home() / ".cache" / "cp-dashboard"),
    )
    args = parser.parse_args()

    cfg = Config(
        username=args.user,
        cache_dir=Path(args.cache_dir),
        output_path=Path(args.output),
    )
    cfg.cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"[fetch_stats] Fetching data for {cfg.username}...", file=sys.stderr)

    # --- Fetch all data ---
    ratings = fetch_rating_history(cfg)
    submissions = fetch_submissions_kenkoooo(cfg)
    difficulties = fetch_difficulties_kenkoooo(cfg)
    problems_list = fetch_problems_kenkoooo(cfg)
    upcoming = fetch_upcoming_contests(cfg)
    tag_overrides = _load_tag_overrides()

    has_submissions = len(submissions) > 0

    print(
        f"[fetch_stats] {len(submissions)} submissions, "
        f"{len(ratings)} rated contests, "
        f"{len(upcoming)} upcoming contests",
        file=sys.stderr,
    )

    # --- Build sections ---
    calendar, streak_days, max_streak = (
        build_streak_calendar(submissions, difficulties)
        if has_submissions
        else ([], 0, 0)
    )

    stats: dict[str, Any] = {
        "generated_at": datetime.now(JST).isoformat(),
        "user": cfg.username,
        "has_submissions": has_submissions,
        "hud": build_hud(submissions, ratings, streak_days, max_streak),
        "player_status": build_player_status(
            submissions, ratings, difficulties, streak_days, max_streak
        ),
        "wa_queue": (
            build_wa_queue(submissions, difficulties, problems_list, tag_overrides)
            if has_submissions
            else []
        ),
        "difficulty_log": (
            build_difficulty_log(submissions, difficulties, ratings)
            if has_submissions
            else {"points": [], "seven_day_avg": [], "current_rating": 0}
        ),
        "tag_ac_rate": (
            build_tag_ac_rate(
                submissions, problems_list, difficulties, tag_overrides
            )
            if has_submissions
            else []
        ),
        "streak_calendar": calendar,
        "speed": (
            build_speed(submissions, ratings) if has_submissions else []
        ),
        "contests": upcoming,
        "rating_history": build_rating_log(ratings),
        "skill_graph": build_skill_graph(
            submissions, difficulties, problems_list, ratings
        ),
    }

    # Atomic write
    tmp = cfg.output_path.with_suffix(".tmp")
    cfg.output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    os.replace(str(tmp), str(cfg.output_path))

    print(f"[fetch_stats] Written to {cfg.output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()

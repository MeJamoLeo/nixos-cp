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
        diff = difficulties.get(pid, {}).get("difficulty", 0)
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
            diff = difficulties.get(pid, {}).get("difficulty", 0)
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

    # 7-day rolling average
    seven_day_avg: list[dict] = []
    if points:
        for i, p in enumerate(points):
            cutoff = p["epoch"] - 7 * 86400
            window = [
                pp["difficulty"]
                for pp in points[: i + 1]
                if pp["epoch"] >= cutoff
            ]
            if window:
                seven_day_avg.append({
                    "epoch": p["epoch"],
                    "avg": round(sum(window) / len(window)),
                })

    return {
        "points": points[-90:],
        "seven_day_avg": seven_day_avg[-30:],
        "current_rating": current_rating,
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
        diff = difficulties.get(pid, {}).get("difficulty", 0)
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
        diff = difficulties.get(pid, {}).get("difficulty", 0)
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
    """A-problem solve speed from contest results."""
    # Build contest start times from rating history
    contest_starts: dict[str, int] = {}
    for r in ratings:
        # ContestScreenName format: "abc384.contest.atcoder.jp"
        screen = r.get("ContestScreenName", "")
        cid = screen.split(".")[0] if "." in screen else ""
        end_epoch = r.get("EndTime", 0)
        # For official key format, EndTime might be ISO string
        if isinstance(end_epoch, str):
            try:
                end_epoch = int(
                    datetime.fromisoformat(end_epoch).timestamp()
                )
            except ValueError:
                continue
        # Contest duration is typically 100min for ABC
        if cid:
            contest_starts[cid] = end_epoch - 6000  # approximate start

    a_times: dict[str, list[int]] = {}
    for s in submissions:
        pid = s.get("problem_id", "")
        if not pid.endswith("_a"):
            continue
        if s.get("result") != "AC":
            continue
        cid = s.get("contest_id", "")
        start = contest_starts.get(cid)
        if start is None:
            continue
        solve_time = s["epoch_second"] - start
        if 0 < solve_time < 600:
            month = datetime.fromtimestamp(
                s["epoch_second"], tz=JST
            ).strftime("%Y-%m")
            a_times.setdefault(month, []).append(solve_time)

    result = []
    for month in sorted(a_times.keys()):
        times = a_times[month]
        avg = sum(times) // len(times)
        result.append({
            "month": month,
            "avg_a_seconds": avg,
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


def build_skill_graph() -> dict:
    path = Path.home() / ".cp" / "skill_graph.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"nodes": []}


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
        "skill_graph": build_skill_graph(),
    }

    # Atomic write
    tmp = cfg.output_path.with_suffix(".tmp")
    cfg.output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    os.replace(str(tmp), str(cfg.output_path))

    print(f"[fetch_stats] Written to {cfg.output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()

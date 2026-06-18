#!/usr/bin/env python3
"""CP Dashboard — GTK4 + WebKit6 + gtk4-layer-shell renderer for Sway BACKGROUND layer.

Supports watchlist: preloads stats for multiple users, switch via external signal.
"""

import json
import os
import re
import shlex
import subprocess
import threading
from ctypes import CDLL
from ctypes.util import find_library

# gtk4-layer-shell must be pre-loaded before GI import.
_lib = find_library('gtk4-layer-shell')
if _lib:
    CDLL(_lib)
else:
    for name in ('libgtk4-layer-shell.so', 'libgtk4-layer-shell.so.0'):
        try:
            CDLL(name)
            break
        except OSError:
            continue

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('WebKit', '6.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, GLib, WebKit, Gtk4LayerShell

DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_HTML = os.path.join(DASHBOARD_DIR, 'dashboard.html')
WATCHLIST_JSON = os.path.join(DASHBOARD_DIR, 'watchlist.json')
CACHE_DIR = os.path.expanduser('~/.cache/cp-dashboard')
SWITCH_FILE = os.path.join(CACHE_DIR, 'switch_user')
NOVISTEPS_PATH = os.path.join(CACHE_DIR, 'novisteps.json')

# ---------------------------------------------------------------------------
# Watchlist & user data cache
# ---------------------------------------------------------------------------

_user_data: dict[str, str] = {}  # username -> JSON string
_current_user: str = ''
_watchlist: list[str] = []
_novi_data: str = ''  # NoviSteps JSON string (single user)
_novi_cookie_warned: bool = False  # mirrored from cookie_expired field in JSON
_novi_watch_interval: float = 5.0  # seconds between mtime checks
_windows: dict = {}  # connector name -> (Gtk.Window, WebKit.WebView)


def _load_novi() -> None:
    """Read novisteps.json into memory and mirror cookie_expired flag."""
    global _novi_data, _novi_cookie_warned
    if not os.path.exists(NOVISTEPS_PATH):
        return
    try:
        with open(NOVISTEPS_PATH) as f:
            _novi_data = f.read()
    except OSError:
        return
    try:
        _novi_cookie_warned = bool(json.loads(_novi_data).get('cookie_expired', False))
    except json.JSONDecodeError:
        pass


def _novi_watch_start() -> None:
    """Reload novisteps.json + re-inject whenever the file changes on disk."""
    import time

    def _loop():
        try:
            last_mtime = os.path.getmtime(NOVISTEPS_PATH)
        except OSError:
            last_mtime = 0.0
        while True:
            time.sleep(_novi_watch_interval)
            try:
                mtime = os.path.getmtime(NOVISTEPS_PATH)
            except OSError:
                continue
            if mtime == last_mtime:
                continue
            last_mtime = mtime
            _load_novi()
            GLib.idle_add(lambda: (_inject_all() or False))
            print('[dashboard] novi: reloaded from disk')

    threading.Thread(target=_loop, daemon=True).start()


def _load_watchlist() -> list[str]:
    try:
        with open(WATCHLIST_JSON) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return []


def _stats_path(username: str) -> str:
    return os.path.join(CACHE_DIR, f'stats_{username}.json')


def _fetch_user(username: str) -> None:
    """Fetch stats for a user (runs in background thread)."""
    out = _stats_path(username)
    try:
        subprocess.run(
            ['nix-shell', '--run',
             f'python fetch_stats.py --user {shlex.quote(username)} --output {shlex.quote(str(out))}'],
            cwd=DASHBOARD_DIR,
            capture_output=True, timeout=120,
        )
        if os.path.exists(out):
            with open(out) as f:
                _user_data[username] = f.read()
            print(f'[dashboard] fetched {username}')
    except Exception as e:
        print(f'[dashboard] fetch error {username}: {e}')


def _prefetch_all() -> None:
    """Load cached data immediately, then refresh all in background."""
    global _current_user
    if not _watchlist:
        return
    _current_user = _watchlist[0]

    # Load ALL cached data immediately (for instant display + switch)
    for user in _watchlist:
        path = _stats_path(user)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    _user_data[user] = f.read()
                print(f'[dashboard] loaded cached {user}')
            except OSError:
                pass

    # Also check old stats.json as fallback for primary user
    primary = _watchlist[0]
    if primary not in _user_data:
        old_path = os.path.join(CACHE_DIR, 'stats.json')
        if os.path.exists(old_path):
            try:
                with open(old_path) as f:
                    _user_data[primary] = f.read()
                print(f'[dashboard] loaded fallback stats.json for {primary}')
            except OSError:
                pass

    # Refresh all users in background threads
    for user in _watchlist:
        t = threading.Thread(target=_fetch_user, args=(user,), daemon=True)
        t.start()


# ---------------------------------------------------------------------------
# WebView injection
# ---------------------------------------------------------------------------

def _inject(webview: WebKit.WebView, username: str | None = None) -> None:
    """Inject stats data for given user and call hydrate()."""
    user = username or _current_user
    data = _user_data.get(user)
    if not data:
        return

    w = webview.get_width()
    h = webview.get_height()

    novi_js = (
        f'window.__NOVI_DATA = {json.dumps(json.loads(_novi_data))};'
        if _novi_data else 'window.__NOVI_DATA = null;'
    ) + f'window.__NOVI_COOKIE_EXPIRED = {str(_novi_cookie_warned).lower()};'
    js = (
        'try {'
        f'window.__VP = {{w:{w}, h:{h}}};'
        f'window.__CP_DATA = {json.dumps(json.loads(data))};'
        f'{novi_js}'
        'hydrate();'
        '} catch(e) {}'
    )
    webview.evaluate_javascript(js, -1, None, None, None, None, None)


def _inject_all(username: str | None = None) -> None:
    for _win, wv in _windows.values():
        _inject(wv, username)


# ---------------------------------------------------------------------------
# Switch user detection
# ---------------------------------------------------------------------------

def _check_switch() -> bool:
    """Check if a user switch was requested via SWITCH_FILE."""
    global _current_user
    if not os.path.exists(SWITCH_FILE):
        return True
    try:
        with open(SWITCH_FILE) as f:
            requested = f.read().strip()
        os.remove(SWITCH_FILE)
        # Validate: only allow watchlist users or 'next'
        if not re.match(r'^[A-Za-z0-9_-]+$', requested):
            return True
        if requested not in _watchlist and requested != 'next':
            return True
        if requested and requested != _current_user:
            if requested in _user_data:
                _current_user = requested
                print(f'[dashboard] switching to {requested}')
                _inject_all(requested)
            elif requested == 'next':
                # Cycle to next user
                idx = _watchlist.index(_current_user) if _current_user in _watchlist else -1
                next_user = _watchlist[(idx + 1) % len(_watchlist)]
                if next_user in _user_data:
                    _current_user = next_user
                    print(f'[dashboard] cycling to {next_user}')
                    _inject_all(next_user)
    except (OSError, ValueError):
        pass
    return True


# ---------------------------------------------------------------------------
# Auto-refresh: watch primary user's stats file for changes
# ---------------------------------------------------------------------------

_last_mtime: float = 0.0


def _watch_stats() -> bool:
    """Watch primary user's stats file for changes."""
    global _last_mtime
    primary = _watchlist[0] if _watchlist else ''
    path = _stats_path(primary)
    if not os.path.exists(path):
        return True
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return True
    if mtime > _last_mtime:
        if _last_mtime > 0:
            # Reload the data
            try:
                with open(path) as f:
                    _user_data[primary] = f.read()
                if _current_user == primary:
                    print(f'[dashboard] stats updated, refreshing')
                    _inject_all(primary)
            except OSError:
                pass
        _last_mtime = mtime
    return True


# ---------------------------------------------------------------------------
# GTK setup
# ---------------------------------------------------------------------------

def _adjust_zoom(webview: WebKit.WebView) -> None:
    """Measure the CSS viewport vs the GTK widget size and compensate via
    set_zoom_level. Some monitors trigger an implicit DPI scale in WebKit even
    when the GTK scale factor is 1, halving the CSS viewport — that breaks
    layout assumptions. After this runs, CSS px ≈ device px on every monitor.
    """
    widget_w = webview.get_width()
    if widget_w <= 0:
        GLib.timeout_add(200, lambda: _inject(webview) or False)
        return

    def cb(wv, result):
        try:
            value = wv.evaluate_javascript_finish(result)
            inner_w = int(value.to_double()) if value is not None else 0
        except Exception:
            inner_w = 0
        if inner_w > 0:
            ratio = widget_w / inner_w
            if ratio > 1.05 or ratio < 0.95:
                target = max(0.25, min(1.0, 1.0 / ratio))
                wv.set_zoom_level(target)
        _inject(wv)

    webview.evaluate_javascript('window.innerWidth', -1, None, None, None, cb)


def _on_load_changed(
    webview: WebKit.WebView,
    event: WebKit.LoadEvent,
) -> None:
    if event == WebKit.LoadEvent.FINISHED:
        GLib.timeout_add(200, lambda: _adjust_zoom(webview) or False)


def _create_dashboard_window(app: Gtk.Application, monitor) -> tuple:
    """Build one dashboard window pinned to `monitor` (or compositor-picked if None).
    Returns (window, webview)."""
    win = Gtk.Window(application=app)
    win.set_title("dashboard")

    Gtk4LayerShell.init_for_window(win)
    Gtk4LayerShell.set_layer(win, Gtk4LayerShell.Layer.BACKGROUND)
    if monitor is not None:
        Gtk4LayerShell.set_monitor(win, monitor)
    Gtk4LayerShell.set_anchor(win, Gtk4LayerShell.Edge.TOP,    True)
    Gtk4LayerShell.set_anchor(win, Gtk4LayerShell.Edge.BOTTOM, True)
    Gtk4LayerShell.set_anchor(win, Gtk4LayerShell.Edge.LEFT,   True)
    Gtk4LayerShell.set_anchor(win, Gtk4LayerShell.Edge.RIGHT,  True)
    Gtk4LayerShell.set_exclusive_zone(win, -1)

    webview = WebKit.WebView()
    settings = webview.get_settings()
    settings.set_property('hardware-acceleration-policy',
                          WebKit.HardwareAccelerationPolicy.NEVER)
    settings.set_property('allow-file-access-from-file-urls', True)
    webview.set_settings(settings)
    webview.load_uri(f'file://{DASHBOARD_HTML}')

    bg = Gdk.RGBA()
    bg.red, bg.green, bg.blue, bg.alpha = 0.008, 0.016, 0.016, 1.0
    webview.set_background_color(bg)

    webview.connect('load-changed', _on_load_changed)

    win.set_child(webview)
    win.present()
    return win, webview


def _monitor_key(monitor, idx: int) -> str:
    if monitor is not None and hasattr(monitor, 'get_connector'):
        connector = monitor.get_connector()
        if connector:
            return connector
    return f'_idx{idx}'


def _reconcile_monitors(app: Gtk.Application, monitors) -> None:
    """Sync `_windows` with the current monitor list. Adds windows for newly
    attached outputs and tears down windows for outputs that disappeared."""
    n = monitors.get_n_items()
    current: dict = {}
    for i in range(n):
        m = monitors.get_item(i)
        current[_monitor_key(m, i)] = m

    for key in list(_windows.keys()):
        if key not in current:
            win, _wv = _windows.pop(key)
            print(f'[dashboard] removing window for {key}')
            win.close()

    for key, m in current.items():
        if key not in _windows:
            print(f'[dashboard] adding window for {key}')
            _windows[key] = _create_dashboard_window(app, m)


def on_activate(app: Gtk.Application) -> None:
    display = Gdk.Display.get_default()
    monitors = display.get_monitors() if display is not None else None

    if monitors is None:
        _windows['_fallback'] = _create_dashboard_window(app, None)
    else:
        monitors.connect('items-changed',
                         lambda *_a: _reconcile_monitors(app, monitors))
        _reconcile_monitors(app, monitors)
        if not _windows:
            # No outputs enumerated yet — let the compositor place one window;
            # items-changed will add per-monitor windows once they appear.
            _windows['_fallback'] = _create_dashboard_window(app, None)

    GLib.timeout_add_seconds(10, _watch_stats)
    GLib.timeout_add(500, _check_switch)
    _novi_watch_start()


def main() -> None:
    global _watchlist
    os.makedirs(CACHE_DIR, exist_ok=True)
    _watchlist = _load_watchlist()
    _load_novi()
    print(f'[dashboard] watchlist: {_watchlist}')
    _prefetch_all()

    app = Gtk.Application(application_id='com.treo.cpdashboard')
    app.connect('activate', on_activate)
    app.run(None)


if __name__ == '__main__':
    main()

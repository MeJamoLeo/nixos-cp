#!/usr/bin/env python3
"""CP Dashboard — GTK4 + WebKit6 + gtk4-layer-shell renderer for Sway BACKGROUND layer.

Supports watchlist: preloads stats for multiple users, switch via external signal.
"""

import json
import os
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

# ---------------------------------------------------------------------------
# Watchlist & user data cache
# ---------------------------------------------------------------------------

_user_data: dict[str, str] = {}  # username -> JSON string
_current_user: str = ''
_watchlist: list[str] = []


def _load_watchlist() -> list[str]:
    try:
        with open(WATCHLIST_JSON) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return ['MeJamoLeo']


def _stats_path(username: str) -> str:
    return os.path.join(CACHE_DIR, f'stats_{username}.json')


def _fetch_user(username: str) -> None:
    """Fetch stats for a user (runs in background thread)."""
    out = _stats_path(username)
    try:
        subprocess.run(
            ['nix-shell', '--run',
             f'python fetch_stats.py --user {username} --output {out}'],
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
    """Fetch primary user first, then others in background."""
    global _current_user
    if not _watchlist:
        return
    _current_user = _watchlist[0]

    # Primary user: blocking fetch (need it for initial display)
    primary = _watchlist[0]
    path = _stats_path(primary)
    # Use cached if fresh enough (< 5 min)
    if os.path.exists(path):
        try:
            with open(path) as f:
                _user_data[primary] = f.read()
            print(f'[dashboard] loaded cached {primary}')
        except OSError:
            pass

    # Fetch all users in background threads
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

    js = (
        'try {'
        f'window.__VP = {{w:{w}, h:{h}}};'
        f'window.__CP_DATA = {data};'
        'hydrate();'
        '} catch(e) {}'
    )
    webview.evaluate_javascript(js, -1, None, None, None, None, None)


# ---------------------------------------------------------------------------
# Switch user detection
# ---------------------------------------------------------------------------

def _check_switch(webview: WebKit.WebView) -> bool:
    """Check if a user switch was requested via SWITCH_FILE."""
    global _current_user
    if not os.path.exists(SWITCH_FILE):
        return True
    try:
        with open(SWITCH_FILE) as f:
            requested = f.read().strip()
        os.remove(SWITCH_FILE)
        if requested and requested != _current_user:
            if requested in _user_data:
                _current_user = requested
                print(f'[dashboard] switching to {requested}')
                _inject(webview, requested)
            elif requested == 'next':
                # Cycle to next user
                idx = _watchlist.index(_current_user) if _current_user in _watchlist else -1
                next_user = _watchlist[(idx + 1) % len(_watchlist)]
                if next_user in _user_data:
                    _current_user = next_user
                    print(f'[dashboard] cycling to {next_user}')
                    _inject(webview, next_user)
    except (OSError, ValueError):
        pass
    return True


# ---------------------------------------------------------------------------
# Auto-refresh: watch primary user's stats file for changes
# ---------------------------------------------------------------------------

_last_mtime: float = 0.0


def _watch_stats(webview: WebKit.WebView) -> bool:
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
                    _inject(webview, primary)
            except OSError:
                pass
        _last_mtime = mtime
    return True


# ---------------------------------------------------------------------------
# GTK setup
# ---------------------------------------------------------------------------

def _on_load_changed(
    webview: WebKit.WebView,
    event: WebKit.LoadEvent,
) -> None:
    if event == WebKit.LoadEvent.FINISHED:
        GLib.timeout_add(200, lambda: _inject(webview) or False)


def on_activate(app: Gtk.Application) -> None:
    win = Gtk.Window(application=app)
    win.set_title("dashboard")

    Gtk4LayerShell.init_for_window(win)
    Gtk4LayerShell.set_layer(win, Gtk4LayerShell.Layer.BACKGROUND)
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
    GLib.timeout_add_seconds(10, _watch_stats, webview)
    GLib.timeout_add(500, _check_switch, webview)  # check switch every 500ms

    win.set_child(webview)
    win.present()


def main() -> None:
    global _watchlist
    os.makedirs(CACHE_DIR, exist_ok=True)
    _watchlist = _load_watchlist()
    print(f'[dashboard] watchlist: {_watchlist}')
    _prefetch_all()

    app = Gtk.Application(application_id='com.treo.cpdashboard')
    app.connect('activate', on_activate)
    app.run(None)


if __name__ == '__main__':
    main()

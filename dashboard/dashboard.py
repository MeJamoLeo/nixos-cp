#!/usr/bin/env python3
"""CP Dashboard — WebKit2GTK renderer for Sway BACKGROUND layer."""

import json
import os

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GLib, WebKit2, GtkLayerShell

DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_HTML = os.path.join(DASHBOARD_DIR, 'dashboard.html')
DUMMY_STATS_JSON = os.path.join(DASHBOARD_DIR, 'dummy_stats.json')
STATS_JSON = os.path.expanduser('~/.cache/cp-dashboard/stats.json')


def _resolve_stats_path() -> str | None:
    if os.path.exists(DUMMY_STATS_JSON):
        return DUMMY_STATS_JSON
    if os.path.exists(STATS_JSON):
        return STATS_JSON
    return None


def _inject(webview: WebKit2.WebView) -> None:
    """Inject viewport size + stats data, then call hydrate()."""
    # ウィンドウの実際のサイズを取得してJSに渡す
    alloc = webview.get_allocation()
    w, h = alloc.width, alloc.height

    # get_allocation()はGDK論理ピクセルを返す。
    # HiDPI scale 2の場合、CSSピクセルと一致するか確認。
    # WebKit2GTKのCSSピクセルはGDK論理ピクセルと同じはず。
    # ただし#rootに固定px指定するとbody(100%)より小さくなる場合がある。
    # bodyは100%で全体を占めるので、rootもwidth/heightを100%にする方が安全。
    print(f'[dashboard] allocation: {w}x{h}')
    parts = [f'window.__VP = {{w:{w}, h:{h}}};']

    path = _resolve_stats_path()
    if path:
        try:
            with open(path) as f:
                parts.append(f'window.__CP_DATA = {f.read()};')
        except OSError:
            pass

    parts.append('hydrate();')
    js = 'try {' + ''.join(parts) + '} catch(e) {}'
    webview.run_javascript(js, None, None, None)

    # デバッグ: HUDサイズ確認
    def _check_hud():
        debug_js = """
        var h = document.querySelector('.hud');
        var s = document.querySelector('.hud-section');
        var l = document.querySelector('.hud-label');
        var v = document.querySelector('.hud-value');
        document.title = 'hud:' + (h?h.offsetHeight:'?') + 'x' + (h?h.offsetWidth:'?')
            + ' sec:' + (s?s.offsetHeight:'?')
            + ' lbl:' + (l?l.offsetHeight:'?') + '/' + (l?l.offsetWidth:'?')
            + ' val:' + (v?v.offsetHeight:'?');
        """
        webview.run_javascript(debug_js, None, None, None)
        GLib.timeout_add(500, lambda: print(f'[debug] {webview.get_title()}') or False)
        return False
    GLib.timeout_add(3000, _check_hud)


def _on_load_changed(
    webview: WebKit2.WebView,
    event: WebKit2.LoadEvent,
) -> None:
    if event == WebKit2.LoadEvent.FINISHED:
        # 少し待ってからinject（ウィンドウサイズ確定後）
        GLib.timeout_add(200, lambda: _inject(webview) or False)


def _refresh(webview: WebKit2.WebView) -> bool:
    _inject(webview)
    return True


def main() -> None:
    win = Gtk.Window()
    win.set_title("dashboard")

    GtkLayerShell.init_for_window(win)
    GtkLayerShell.set_layer(win, GtkLayerShell.Layer.BACKGROUND)
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.TOP,    True)
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.BOTTOM, True)
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.LEFT,   True)
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.RIGHT,  True)
    GtkLayerShell.set_exclusive_zone(win, -1)

    webview = WebKit2.WebView()
    settings = webview.get_settings()
    settings.set_property('hardware-acceleration-policy',
                          WebKit2.HardwareAccelerationPolicy.NEVER)
    settings.set_property('default-font-size', 16)
    settings.set_property('default-monospace-font-size', 13)
    webview.set_settings(settings)
    webview.load_uri(f'file://{DASHBOARD_HTML}')
    webview.set_background_color(
        Gdk.RGBA(red=0.008, green=0.016, blue=0.016, alpha=1.0)
    )

    webview.connect('load-changed', _on_load_changed)
    GLib.timeout_add_seconds(1800, _refresh, webview)

    win.add(webview)
    win.connect('destroy', Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
import json
import os

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GLib, WebKit2, GtkLayerShell

DASHBOARD_HTML = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'dashboard.html'
        )
STATS_JSON = os.path.expanduser('~/.cache/cp-dashboard/stats.json')


def _inject_data(webview: WebKit2.WebView) -> None:
    """Read stats.json and inject into the webview."""
    if not os.path.exists(STATS_JSON):
        print('[dashboard] stats.json not found')
        return
    try:
        with open(STATS_JSON) as f:
            data = f.read()
        print(f'[dashboard] injecting {len(data)} bytes of JSON')
        js = f'window.__CP_DATA = {data}; hydrate();'
        webview.run_javascript(js, None, None, None)
        print('[dashboard] injection done')
    except Exception as e:
        print(f'[dashboard] inject error: {e}')


def _on_load_changed(
    webview: WebKit2.WebView,
    event: WebKit2.LoadEvent,
) -> None:
    if event == WebKit2.LoadEvent.FINISHED:
        _inject_data(webview)


def _refresh_data(webview: WebKit2.WebView) -> bool:
    """Periodic refresh callback (every 30 minutes)."""
    _inject_data(webview)
    return True  # keep the timer running


def main() -> None:
    win = Gtk.Window()
    win.set_title("dashboard")

    # gtk-layer-shellでBACKGROUNDレイヤーに固定
    GtkLayerShell.init_for_window(win)
    GtkLayerShell.set_layer(win, GtkLayerShell.Layer.BACKGROUND)
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.TOP,    True)
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.BOTTOM, True)
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.LEFT,   True)
    GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.RIGHT,  True)
    GtkLayerShell.set_exclusive_zone(win, -1)

    # HTMLをロード
    webview = WebKit2.WebView()
    settings = webview.get_settings()
    settings.set_property('hardware-acceleration-policy',
                          WebKit2.HardwareAccelerationPolicy.NEVER)
    webview.set_settings(settings)
    webview.load_uri(f'file://{DASHBOARD_HTML}')
    webview.set_background_color(Gdk.RGBA(red=0.008, green=0.016, blue=0.016, alpha=1.0))

    # データ注入: ページロード完了時 + 30分ごと
    webview.connect('load-changed', _on_load_changed)
    GLib.timeout_add_seconds(1800, _refresh_data, webview)

    win.add(webview)
    win.connect('destroy', Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()

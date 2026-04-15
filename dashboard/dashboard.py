#!/usr/bin/env python3
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
    """Return the stats JSON path, preferring dummy data if it exists."""
    if os.path.exists(DUMMY_STATS_JSON):
        return DUMMY_STATS_JSON
    if os.path.exists(STATS_JSON):
        return STATS_JSON
    return None


def _inject_data(webview: WebKit2.WebView) -> None:
    """Read stats.json and inject into the webview."""
    path = _resolve_stats_path()
    if path is None:
        return
    try:
        with open(path) as f:
            data = f.read()
        scale_js = """
        document.querySelectorAll('*').forEach(function(el) {
            var fs = el.style.fontSize;
            if (fs && fs.endsWith('px')) {
                var val = parseFloat(fs);
                if (val > 0) el.style.fontSize = (val * 1.5) + 'px';
            }
        });
        """
        js = f'try {{ window.__CP_DATA = {data}; hydrate(); {scale_js} }} catch(e) {{}}'
        webview.run_javascript(js, None, None, None)
    except (OSError, ValueError):
        pass


def _on_load_changed(
    webview: WebKit2.WebView,
    event: WebKit2.LoadEvent,
) -> None:
    if event == WebKit2.LoadEvent.FINISHED:
        _inject_data(webview)
        # hydrate後のDOMを/tmp/rendered.htmlに保存
        def _save_dom(wv, result, _ud):
            try:
                r = wv.run_javascript_finish(result)
                html = r.get_js_value().to_string()
                with open('/tmp/rendered.html', 'w') as f:
                    f.write(html)
                print(f'[dashboard] DOM saved: {len(html)} bytes')
            except Exception as e:
                print(f'[dashboard] DOM save error: {e}')
        GLib.timeout_add(500, lambda: webview.run_javascript(
            'document.documentElement.outerHTML',
            None, _save_dom, None
        ) or False)


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
    settings.set_property('default-font-size', 24)
    settings.set_property('default-monospace-font-size', 20)
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

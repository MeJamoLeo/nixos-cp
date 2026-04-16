#!/usr/bin/env python3
"""CP Dashboard — GTK4 + WebKit6 + gtk4-layer-shell renderer for Sway BACKGROUND layer."""

import os
import sys

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('WebKit', '6.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, GLib, WebKit, Gtk4LayerShell

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


def _inject(webview: WebKit.WebView) -> None:
    """Inject viewport size + stats data, then call hydrate()."""
    w = webview.get_width()
    h = webview.get_height()
    print(f'[dashboard] webview size: {w}x{h}')

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
    webview.evaluate_javascript(js, -1, None, None, None, None, None)


def _debug_check(webview: WebKit.WebView) -> bool:
    """デバッグ情報を取得してファイルに書き出す"""
    debug_js = """
    (function() {
        var info = {};
        info.dpr = window.devicePixelRatio;
        info.innerW = window.innerWidth;
        info.innerH = window.innerHeight;
        info.screenW = screen.width;
        info.screenH = screen.height;

        var body = document.body;
        if (body) {
            var cs = getComputedStyle(body);
            info.bodyFontSize = cs.fontSize;
            info.bodyWidth = cs.width;
            info.bodyHeight = cs.height;
            info.bodyOffsetW = body.offsetWidth;
            info.bodyOffsetH = body.offsetHeight;
        }

        var rating = document.querySelector('.ps-rating');
        if (rating) {
            var rcs = getComputedStyle(rating);
            info.ratingFontSize = rcs.fontSize;
            info.ratingOffsetH = rating.offsetHeight;
            info.ratingOffsetW = rating.offsetWidth;
            info.ratingText = rating.textContent;
        }

        var hud = document.querySelector('.hud');
        if (hud) {
            info.hudOffsetH = hud.offsetHeight;
        }

        var label = document.querySelector('.hud-label');
        if (label) {
            var lcs = getComputedStyle(label);
            info.labelFontSize = lcs.fontSize;
            info.labelOffsetH = label.offsetHeight;
        }

        var root = getComputedStyle(document.documentElement);
        info.varFs3xl = root.getPropertyValue('--fs-3xl');
        info.varFsSm = root.getPropertyValue('--fs-sm');
        info.varFsLg = root.getPropertyValue('--fs-lg');

        return JSON.stringify(info, null, 2);
    })();
    """
    def _on_debug(wv, result, _ud=None):
        try:
            js_val = wv.evaluate_javascript_finish(result)
            text = js_val.to_string() if js_val else 'null'
            print(f'[DEBUG] {text}')
            with open('/tmp/debug_info.json', 'w') as f:
                f.write(text)
        except Exception as e:
            print(f'[DEBUG ERROR] {e}')

    webview.evaluate_javascript(debug_js, -1, None, None, None, _on_debug, None)
    return False


def _on_load_changed(
    webview: WebKit.WebView,
    event: WebKit.LoadEvent,
) -> None:
    if event == WebKit.LoadEvent.FINISHED:
        GLib.timeout_add(200, lambda: _inject(webview) or False)
        GLib.timeout_add(5000, lambda: _debug_check(webview) or False)


def _refresh(webview: WebKit.WebView) -> bool:
    _inject(webview)
    return True


def on_activate(app: Gtk.Application) -> None:
    win = Gtk.ApplicationWindow(application=app)
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
    webview.set_settings(settings)
    webview.load_uri(f'file://{DASHBOARD_HTML}')

    # GTK4: set_background_color → WebView背景はCSS側で制御
    webview.set_background_color(
        Gdk.RGBA(red=0.008, green=0.016, blue=0.016, alpha=1.0)
    )

    webview.connect('load-changed', _on_load_changed)
    GLib.timeout_add_seconds(1800, _refresh, webview)

    win.set_child(webview)
    win.present()


def main() -> None:
    app = Gtk.Application(application_id='com.treo.cpdashboard')
    app.connect('activate', on_activate)
    app.run(None)


if __name__ == '__main__':
    main()

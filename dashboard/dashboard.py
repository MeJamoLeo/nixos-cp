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

    # layer-shellのviewportバグ回避:
    # WebKit2GTKがgeometry hints(-1)を負の値として解釈するため
    # CSS全体の寸法が負になる。get_allocation()の正しい値を
    # html/bodyに直接px指定して強制上書きする。
    # さらに全てのCSS変数をabsolute pxに変換し、
    # フォントサイズも直接style属性で強制する。
    parts.append(
        f"document.documentElement.style.cssText="
        f"'width:{w}px !important;height:{h}px !important;"
        f"overflow:hidden;font-size:80px !important;';"
        f"document.body.style.cssText="
        f"'width:{w}px !important;height:{h}px !important;"
        f"margin:0;padding:0;overflow:hidden;font-size:80px !important;';"
    )
    parts.append('hydrate();')
    js = 'try {' + ''.join(parts) + '} catch(e) {}'
    webview.run_javascript(js, None, None, None)


def _debug_check(webview: WebKit2.WebView) -> bool:
    """複数のデバッグ情報を取得してファイルに書き出す"""
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

        // CSS変数の実際の値
        var root = getComputedStyle(document.documentElement);
        info.varFs3xl = root.getPropertyValue('--fs-3xl');
        info.varFsSm = root.getPropertyValue('--fs-sm');
        info.varFsLg = root.getPropertyValue('--fs-lg');

        // 結果をファイルに書くためtitleに入れる
        var out = JSON.stringify(info, null, 2);
        document.title = 'DEBUG_DONE';

        // DOM要素として書き出す（titleが取れない場合の保険）
        var pre = document.createElement('pre');
        pre.id = 'debug-output';
        pre.style.cssText = 'position:fixed;bottom:0;left:0;background:red;color:white;font-size:20px;z-index:9999;padding:10px;max-height:50%;overflow:auto;';
        pre.textContent = out;
        document.body.appendChild(pre);

        return out;
    })();
    """
    def _on_debug(wv, result, _ud):
        try:
            r = wv.run_javascript_finish(result)
            val = r.get_js_value()
            text = val.to_string() if val else 'null'
            print(f'[DEBUG] {text}')
            # ファイルにも書き出す
            with open('/tmp/debug_info.json', 'w') as f:
                f.write(text)
        except Exception as e:
            print(f'[DEBUG ERROR] {e}')

    webview.run_javascript(debug_js, None, _on_debug, None)
    return False


def _on_load_changed(
    webview: WebKit2.WebView,
    event: WebKit2.LoadEvent,
) -> None:
    if event == WebKit2.LoadEvent.FINISHED:
        # 少し待ってからinject（ウィンドウサイズ確定後）
        GLib.timeout_add(200, lambda: _inject(webview) or False)
        GLib.timeout_add(5000, lambda: _debug_check(webview) or False)


def _refresh(webview: WebKit2.WebView) -> bool:
    _inject(webview)
    return True


def _get_monitor_size() -> tuple[int, int]:
    """Get primary monitor size in logical pixels."""
    display = Gdk.Display.get_default()
    if display:
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        if monitor:
            geom = monitor.get_geometry()
            return geom.width, geom.height
    # fallback: X1 Carbon Nano at scale 1
    return 2160, 1350


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

    # GtkFixed wrapper: layer-shellのgeometry hints(-1)が
    # WebKit2GTKの内部viewport計算を壊す問題を回避。
    # WebViewを直接windowに入れず、Fixedコンテナ経由で
    # 明示的なサイズを渡すことで正のviewportを維持する。
    mon_w, mon_h = _get_monitor_size()
    print(f'[dashboard] monitor size: {mon_w}x{mon_h}')

    fixed = Gtk.Fixed()
    win.add(fixed)

    webview = WebKit2.WebView()
    webview.set_size_request(mon_w, mon_h)

    settings = webview.get_settings()
    settings.set_property('hardware-acceleration-policy',
                          WebKit2.HardwareAccelerationPolicy.NEVER)
    settings.set_property('default-font-size', 80)
    settings.set_property('default-monospace-font-size', 64)
    settings.set_property('enable-smooth-scrolling', False)
    webview.set_settings(settings)
    webview.load_uri(f'file://{DASHBOARD_HTML}')
    webview.set_background_color(
        Gdk.RGBA(red=0.008, green=0.016, blue=0.016, alpha=1.0)
    )

    webview.connect('load-changed', _on_load_changed)
    GLib.timeout_add_seconds(1800, _refresh, webview)

    fixed.put(webview, 0, 0)
    win.connect('destroy', Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()

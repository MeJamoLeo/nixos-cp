#!/usr/bin/env python3
import os
os.environ['GDK_SCALE'] = '1'
os.environ['GDK_DPI_SCALE'] = '1'
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, WebKit2, GtkLayerShell

DASHBOARD_HTML = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'dashboard.html'
        )

def main():
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
    try:
        with open(DASHBOARD_HTML, 'r') as f:
            html = f.read()
        webview.load_html(html, f'file://{os.path.dirname(DASHBOARD_HTML)}/')
    except FileNotFoundError:
        webview.load_html('<h1 style="color:white;background:black">HTML file not found</h1>', None)
    win.add(webview)

    win.connect('destroy', Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()

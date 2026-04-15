#!/usr/bin/env python3
import os
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, WebKit2, GtkLayerShell

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
    settings = webview.get_settings()
    settings.set_property('hardware-acceleration-policy',
                          WebKit2.HardwareAccelerationPolicy.NEVER)
    webview.set_settings(settings)
    webview.load_uri(f'file://{DASHBOARD_HTML}')
    webview.set_background_color(Gdk.RGBA(red=0.008, green=0.016, blue=0.016, alpha=1.0))
    win.add(webview)

    win.connect('destroy', Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()

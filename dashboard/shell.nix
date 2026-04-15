{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    (python3.withPackages (ps: with ps; [
      pygobject3
      pycairo
    ]))
    gtk3
    webkitgtk_4_1
    gtk-layer-shell
    gobject-introspection
  ];
}

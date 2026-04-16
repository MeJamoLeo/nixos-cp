{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    (python3.withPackages (ps: with ps; [
      pygobject3
      pycairo
    ]))
    gtk4
    webkitgtk_6_0
    gtk4-layer-shell
    gobject-introspection
  ];
}

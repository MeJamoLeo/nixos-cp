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

  # gtk4-layer-shell must be on LD_LIBRARY_PATH for ctypes preload
  shellHook = ''
    export LD_LIBRARY_PATH="${pkgs.gtk4-layer-shell}/lib:$LD_LIBRARY_PATH"
  '';
}

{ config, pkgs, lib, claude-code-pkg, ... }:

{
  imports = [
    ../../profiles/full/home.nix
  ];

  home.packages = [
    claude-code-pkg
  ];
}

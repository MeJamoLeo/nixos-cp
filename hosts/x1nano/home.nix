{ config, pkgs, lib, claude-code-pkg, ... }:

{
  imports = [
    ../../profiles/full/home.nix
  ];

  home.packages = [
    claude-code-pkg
  ];

  # CP snippets: symlink ~/cp/snippets → ~/nixos-cp/snippets so editing
  # the file in the repo is immediately picked up by LuaSnip without
  # going through the Nix store (no rebuild needed per snippet edit).
  home.file."cp/snippets".source =
    config.lib.file.mkOutOfStoreSymlink
      "${config.home.homeDirectory}/nixos-cp/snippets";
}

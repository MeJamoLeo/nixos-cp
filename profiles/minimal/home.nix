{ config, pkgs, ... }:

{
  imports = [
    ../../home/shell.nix
    ../../home/git.nix
  ];

  home.username = "treo";
  home.homeDirectory = "/home/treo";

  home.packages = with pkgs; [
    htop
    git
    python3
    fzf
    online-judge-tools
  ];

  programs.home-manager.enable = true;

  home.stateVersion = "24.11";
}

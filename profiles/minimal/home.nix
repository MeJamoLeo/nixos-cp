{ config, pkgs, ... }:

{
  imports = [
    ../../home/shell.nix
    ../../home/git.nix
  ];

  home.username = "treo";
  home.homeDirectory = "/home/treo";

  # Make cp-* tools visible to non-interactive shells (e.g. nvim `:!`).
  # ~/.zshrc only runs for interactive zsh, so the PATH export there
  # is invisible to nvim-spawned shells; sessionPath fixes that via
  # ~/.profile and home-manager session variables.
  home.sessionPath = [ "$HOME/nixos-cp/tools" ];

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

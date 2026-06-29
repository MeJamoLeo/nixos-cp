{ config, pkgs, ... }:

{
  imports = [
    ../minimal/home.nix
    ../../home/starship.nix
    ../../home/kitty.nix
    ../../home/dashboard.nix
    ../../home/claude.nix
    ../../modules/sway.nix
    ../../modules/kanshi.nix
    ../../modules/nvim
  ];

  home.packages = with pkgs; [
    wofi
    wl-clipboard
    jq
    zed-editor
  ];
}

{ config, pkgs, ... }:

{
  imports = [
    ../minimal/home.nix
    ../../home/starship.nix
    ../../modules/sway.nix
    ../../modules/nvim
  ];

  home.packages = with pkgs; [
    kitty
    wofi
    wl-clipboard
  ];
}

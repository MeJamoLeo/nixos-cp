{ config, pkgs, ... }:

{
  imports = [
    ../minimal/home.nix
    ../../home/starship.nix
    ../../home/kitty.nix
    ../../home/dashboard.nix
    ../../modules/sway.nix
    ../../modules/nvim
  ];

  home.packages = with pkgs; [
    wofi
    wl-clipboard
  ];
}

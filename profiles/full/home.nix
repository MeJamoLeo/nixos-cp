{ config, pkgs, ... }:

{
  imports = [
    ../minimal/home.nix
    ../../home/starship.nix
    ../../home/firefox.nix
    ../../modules/sway.nix
    ../../modules/nvim
  ];
}

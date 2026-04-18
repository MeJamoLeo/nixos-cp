{ config, pkgs, ... }:

{
  imports = [
    ../minimal/home.nix
    ../../home/starship.nix
    ../../modules/sway.nix
    ../../modules/nvim
  ];
}

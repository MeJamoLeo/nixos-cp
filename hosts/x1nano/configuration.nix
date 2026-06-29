{ config, pkgs, ... }:

{
  imports = [
    ../../profiles/full/configuration.nix
    ./hardware-configuration.nix
  ];

  networking.hostName = "x1nano";

  nixpkgs.config.allowUnfreePredicate = pkg:
    builtins.elem (pkgs.lib.getName pkg) [ "obsidian" ];

  # Fingerprint authentication
  services.fprintd.enable = true;
  security.pam.services.login.fprintAuth = true;
  security.pam.services.sudo.fprintAuth = true;

  # Power management
  services.tlp.enable = true;
}

{ config, pkgs, ... }:

{
  imports = [
    ../../profiles/minimal/configuration.nix
  ];

  networking.hostName = "cp-minimal";
}

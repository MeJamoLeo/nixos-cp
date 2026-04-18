{ config, pkgs, ... }:

{
  imports = [
    ../../profiles/full/configuration.nix
  ];

  networking.hostName = "cp-full";
}

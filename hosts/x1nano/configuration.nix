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

  # Power management: lean on COSMIC's power-profiles-daemon (UI toggle) rather
  # than TLP. Keep only a battery charge cap for longevity (mostly-docked ssh box).
  services.tlp.enable = false;

  systemd.services.battery-charge-threshold = {
    description = "Cap battery charge at 80% for longevity";
    wantedBy = [ "multi-user.target" ];
    after = [ "multi-user.target" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = "${pkgs.bash}/bin/bash -c 'echo 80 > /sys/class/power_supply/BAT0/charge_control_end_threshold'";
    };
  };

  # Re-apply the cap after resume (suspend can reset it).
  powerManagement.resumeCommands = "echo 80 > /sys/class/power_supply/BAT0/charge_control_end_threshold";
}

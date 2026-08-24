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

  # --- CS4371 security lab -------------------------------------------------
  # VirtualBox hosts the five-VM sandbox (pfSense / Ubuntu / WinXP / Kali /
  # Win95) that CS4371 Project-1 asks for. The Extension Pack is deliberately
  # left out: USB passthrough and VRDP are not needed here, and it is unfree
  # plus a long local build.
  virtualisation.virtualbox.host.enable = true;

  # Non-root packet capture: gives dumpcap capabilities and creates the group.
  programs.wireshark.enable = true;

  users.users.treo.extraGroups = [ "vboxusers" "wireshark" ];

  # VirtualBox keeps its machines under ~/vm-draft on the internal disk. These
  # are throwaway prototypes: the graded build is assembled clean on the
  # portable SSD (ukishima) instead, so this host never needs to know that the
  # SSD exists. Mount it by hand on the rare occasion you want to look:
  #   sudo mount /dev/disk/by-label/vmstore /mnt

  # --- Remote access -------------------------------------------------------
  # DHCP hands this box a fresh address whenever the network changes, so
  # `ssh <ip>` keeps going stale. Tailscale gives it a stable name instead.
  services.tailscale.enable = true;
  networking.firewall.trustedInterfaces = [ "tailscale0" ];
}

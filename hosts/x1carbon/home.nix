{ config, pkgs, lib, ... }:

{
  imports = [
    ../../profiles/full/home.nix
  ];

  systemd.user.services.fetch-stats = {
    Unit = {
      Description = "Fetch AtCoder stats for dashboard";
    };
    Service = {
      Type = "oneshot";
      ExecStart = "${pkgs.nix}/bin/nix-shell /home/treo/nixos-cp/dashboard/shell.nix --run 'bash /home/treo/nixos-cp/dashboard/fetch_all.sh'";
    };
  };

  systemd.user.timers.fetch-stats = {
    Unit = {
      Description = "Fetch AtCoder stats every 2 minutes";
    };
    Timer = {
      OnBootSec = "30s";
      OnUnitActiveSec = "2m";
      Unit = "fetch-stats.service";
    };
    Install = {
      WantedBy = [ "timers.target" ];
    };
  };
}

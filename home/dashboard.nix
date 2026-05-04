{ config, pkgs, ... }:

let
  repoDir = "${config.home.homeDirectory}/nixos-cp";
in
{
  systemd.user.services.fetch-stats = {
    Unit.Description = "Fetch AtCoder stats for dashboard";
    Service = {
      Type = "oneshot";
      WorkingDirectory = "${repoDir}/dashboard";
      ExecStart = "${pkgs.bash}/bin/bash ${repoDir}/dashboard/fetch_all.sh";
    };
  };

  systemd.user.timers.fetch-stats = {
    Unit.Description = "Fetch AtCoder stats every 2 minutes";
    Timer = {
      OnBootSec = "1min";
      OnUnitActiveSec = "2min";
      Unit = "fetch-stats.service";
    };
    Install.WantedBy = [ "timers.target" ];
  };
}

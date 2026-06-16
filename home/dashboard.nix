{ config, pkgs, ... }:

let
  repoDir = "${config.home.homeDirectory}/nixos-cp";
  dashDir = "${repoDir}/dashboard";

  fetchPath = pkgs.lib.makeBinPath [ pkgs.coreutils pkgs.python3 ];

  dashRun = pkgs.writeShellScript "cp-dashboard-run" ''
    exec ${pkgs.nix}/bin/nix-shell ${dashDir}/shell.nix \
      --keep WAYLAND_DISPLAY \
      --keep XDG_RUNTIME_DIR \
      --run "python3 ${dashDir}/dashboard.py"
  '';
in
{
  systemd.user.services.fetch-stats = {
    Unit.Description = "Fetch AtCoder stats for dashboard";
    Service = {
      Type = "oneshot";
      WorkingDirectory = dashDir;
      Environment = "PATH=${fetchPath}";
      ExecStart = "${pkgs.bash}/bin/bash ${dashDir}/fetch_all.sh";
    };
  };

  systemd.user.services.fetch-novisteps = {
    Unit.Description = "Fetch one NoviSteps workbook";
    Service = {
      Type = "oneshot";
      WorkingDirectory = dashDir;
      Environment = "PATH=${fetchPath}";
      ExecStart = "${pkgs.python3}/bin/python3 ${dashDir}/fetch_novisteps.py --one";
    };
  };

  systemd.user.services.cp-dashboard = {
    Unit = {
      Description = "CP dashboard background renderer";
      PartOf = [ "sway-session.target" ];
      After = [ "sway-session.target" ];
    };
    Service = {
      ExecStart = "${dashRun}";
      Restart = "always";
      RestartSec = 3;
    };
    Install.WantedBy = [ "sway-session.target" ];
  };
}

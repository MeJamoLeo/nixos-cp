{...}: {
  programs.starship = {
    enable = true;

    enableBashIntegration = true;
    enableZshIntegration = true;

    settings = {
      format = "$directory$git_branch$git_commit$git_state$git_status$nix_shell$cmd_duration$line_break$jobs$battery\${custom.battery_time}$character";
      character = {
        success_symbol = "[›](bold green)";
        error_symbol = "[›](bold red)";
      };
      aws = {
        symbol = "🅰 ";
      };
      gcloud = {
        # do not show the account/project's info
        # to avoid the leak of sensitive information when sharing the terminal
        format = "on [$symbol$active(\($region\))]($style) ";
        symbol = "🅶 ️";
      };
      battery = {
        full_symbol = "🔋 ";
        charging_symbol = "⚡ ";
        discharging_symbol = "🔋 ";
        unknown_symbol = "❓ ";
        empty_symbol = "💀 ";
        format = "[$symbol$percentage]($style) ";
        display = [
          { threshold = 15; style = "bold red"; discharging_symbol = "💀 "; }
          { threshold = 40; style = "bold yellow"; discharging_symbol = "🪫 "; }
          { threshold = 100; style = "bold green"; discharging_symbol = "🔋 "; }
        ];
      };
      custom.battery_time = {
        command = ''
          st=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null) || exit 0
          [ "$st" = "Full" ] && exit 0
          [ "$st" = "Unknown" ] && exit 0
          en=$(cat /sys/class/power_supply/BAT0/energy_now 2>/dev/null) || exit 0
          pn=$(cat /sys/class/power_supply/BAT0/power_now 2>/dev/null) || exit 0
          [ "$pn" -le 0 ] && exit 0
          if [ "$st" = "Discharging" ]; then
            mins=$((en * 60 / pn))
          else
            ef=$(cat /sys/class/power_supply/BAT0/energy_full)
            mins=$(( (ef - en) * 60 / pn ))
          fi
          printf "%dh%02dm" $((mins/60)) $((mins%60))
        '';
        when = "test -r /sys/class/power_supply/BAT0/power_now";
        format = "[($output)]($style) ";
        style = "dimmed white";
        shell = [ "sh" ];
      };
    };
  };
}

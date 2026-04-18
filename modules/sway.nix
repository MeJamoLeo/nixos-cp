{ config, pkgs, ... }:

{
	wayland.windowManager.sway = {
		enable = true;
		config = {
			modifier = "Mod4"; # Super/Win key (Linux default)

				keybindings = let
				mod = "Mod4";
			in {
				# Focus
				"${mod}+h" = "focus left";
				"${mod}+j" = "focus down";
				"${mod}+k" = "focus up";
				"${mod}+l" = "focus right";

				# Move window
				"${mod}+shift+h" = "move left";
				"${mod}+shift+j" = "move down";
				"${mod}+shift+k" = "move up";
				"${mod}+shift+l" = "move right";

				# Window
				"${mod}+q" = "kill";
				"${mod}+f" = "fullscreen toggle";
				"${mod}+minus" = "layout splitv";
				"${mod}+equal" = "layout splith";

				# Resize
				"${mod}+comma" = "resize shrink width 50px";
				"${mod}+period" = "resize grow width 50px";

				# Workspace (numbers)
				"${mod}+1" = "workspace 1";
				"${mod}+2" = "workspace 2";
				"${mod}+3" = "workspace 3";
				"${mod}+4" = "workspace 4";
				"${mod}+5" = "workspace 5";
				"${mod}+6" = "workspace 6";
				"${mod}+7" = "workspace 7";
				"${mod}+8" = "workspace 8";
				"${mod}+9" = "workspace 9";

				# Move to workspace
				"${mod}+shift+1" = "move container to workspace 1";
				"${mod}+shift+2" = "move container to workspace 2";
				"${mod}+shift+3" = "move container to workspace 3";
				"${mod}+shift+4" = "move container to workspace 4";
				"${mod}+shift+5" = "move container to workspace 5";
				"${mod}+shift+6" = "move container to workspace 6";
				"${mod}+shift+7" = "move container to workspace 7";
				"${mod}+shift+8" = "move container to workspace 8";
				"${mod}+shift+9" = "move container to workspace 9";

				# Apps
				"${mod}+Return" = "exec ~/nixos-cp/tools/open-terminal";
				"${mod}+d" = "exec wofi --show drun";
				"${mod}+b" = "exec firefox";

				# Media keys
				"XF86AudioRaiseVolume" = "exec pactl set-sink-volume @DEFAULT_SINK@ +5%";
				"XF86AudioLowerVolume" = "exec pactl set-sink-volume @DEFAULT_SINK@ -5%";
				"XF86AudioMute" = "exec pactl set-sink-mute @DEFAULT_SINK@ toggle";
				"XF86MonBrightnessUp" = "exec brightnessctl set +10%";
				"XF86MonBrightnessDown" = "exec brightnessctl set 10%-";

				# Session
				"${mod}+shift+q" = "exit";

				# CP practice session (idempotent: focus or create)
				"${mod}+g" = "exec ~/nixos-cp/tools/cp-session";

				# Dashboard: cycle watchlist users
				"${mod}+grave" = "exec ~/nixos-cp/dashboard/switch_user.sh next";
			};

			input = {
				"type:keyboard" = {
					xkb_options = "ctrl:swapcaps";
				};
				"type:touchpad" = {
					natural_scroll = "enabled";
					tap = "enabled";
				};
			};

			gaps = {
				inner = 10;
				outer = 12;
			};

			output."eDP-1".scale = "1";

			terminal = "kitty";

			bars = [];

			window.border = 2;
			colors.focused = {
				border = "#6d28d9";
				background = "#6d28d9";
				text = "#ffffff";
				indicator = "#6d28d9";
				childBorder = "#6d28d9";
			};

			window.commands = [
				{ criteria = { app_id = "firefox"; }; command = "opacity 0.85"; }
				{ criteria = { app_id = "kitty"; }; command = "opacity 0.85"; }
			];

			startup = [
				{ command = "sleep 1 && /run/current-system/sw/bin/fcitx5 -d --replace"; }
				{ command = "sleep 3 && nix-shell /home/treo/nixos-cp/dashboard/shell.nix --keep WAYLAND_DISPLAY --keep XDG_RUNTIME_DIR --run 'python3 /home/treo/nixos-cp/dashboard/dashboard.py'"; }
			];
		};
	};
}

{ config, pkgs, ... }:

{
	wayland.windowManager.sway = {
		enable = true;
		config = {
			modifier = "Mod1"; # alt key

				keybindings = let
				mod = "Mod1";
			in {
				"${mod}+h" = "focus left";
				"${mod}+j" = "focus down";
				"${mod}+k" = "focus up";
				"${mod}+l" = "focus right";

				"${mod}+shift+h" = "move left";
				"${mod}+shift+j" = "move down";
				"${mod}+shift+k" = "move up";
				"${mod}+shift+l" = "move right";

				"${mod}+q" = "kill";
				"${mod}+Return" = "fullscreen toggle";

				"${mod}+minus" = "layout splitv";
				"${mod}+equal" = "layout splith";

				"${mod}+1" = "workspace 1";
				"${mod}+2" = "workspace 2";
				"${mod}+3" = "workspace 3";
				"${mod}+a" = "workspace a";
				"${mod}+b" = "workspace b";
				"${mod}+c" = "workspace c";
				"${mod}+d" = "workspace d";
				"${mod}+e" = "workspace e";
				"${mod}+f" = "workspace f";
				"${mod}+g" = "workspace g";
				"${mod}+i" = "workspace i";
				"${mod}+m" = "workspace m";
				"${mod}+n" = "workspace n";
				"${mod}+o" = "workspace o";
				"${mod}+p" = "workspace p";
				"${mod}+s" = "workspace s";
				"${mod}+t" = "workspace t";
				"${mod}+u" = "workspace u";
				"${mod}+v" = "workspace v";
				"${mod}+w" = "workspace w";
				"${mod}+y" = "workspace y";
				"${mod}+z" = "workspace z";

				"${mod}+shift+1" = "move container to workspace 1";
				"${mod}+shift+2" = "move container to workspace 2";
				"${mod}+shift+3" = "move container to workspace 3";
				"${mod}+shift+a" = "move container to workspace a";
				"${mod}+shift+b" = "move container to workspace b";
				"${mod}+shift+c" = "move container to workspace c";
				"${mod}+shift+d" = "move container to workspace d";
				"${mod}+shift+e" = "move container to workspace e";
				"${mod}+shift+f" = "move container to workspace f";
				"${mod}+shift+g" = "move container to workspace g";
				"${mod}+shift+i" = "move container to workspace i";
				"${mod}+shift+m" = "move container to workspace m";
				"${mod}+shift+o" = "move container to workspace o";
				"${mod}+shift+p" = "move container to workspace p";
				"${mod}+shift+s" = "move container to workspace s";
				"${mod}+shift+t" = "move container to workspace t";
				"${mod}+shift+u" = "move container to workspace u";
				"${mod}+shift+v" = "move container to workspace v";
				"${mod}+shift+w" = "move container to workspace w";
				"${mod}+shift+y" = "move container to workspace y";
				"${mod}+shift+z" = "move container to workspace z";

				"${mod}+comma" = "resize shrink width 50px";
				"${mod}+period" = "resize grow width 50px";

				"${mod}+shift+Return" = "exec kitty";

				"${mod}+shift+q" = "exit";
			};

			gaps = {
				inner = 10;
				outer = 12;
			};

			output."eDP-1".scale = "2";

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

			startup = [
				{ command = "sleep 3 && nix-shell /home/treo/nixos-cp/dashboard/shell.nix --keep WAYLAND_DISPLAY --keep XDG_RUNTIME_DIR --run 'python3 /home/treo/nixos-cp/dashboard/dashboard.py'"; }
			];
		};
	};
}

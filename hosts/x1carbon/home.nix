{ config, pkgs, lib, ... }:

{
	imports = [
		../../home/shell.nix
		../../home/git.nix
		../../home/starship.nix
		../../modules/sway.nix
	];

	home.username = "treo";
	home.homeDirectory = "/home/treo";

	home.packages = with pkgs; [
		htop
	];

	systemd.user.services.fetch-stats = {
		Unit = {
			Description = "Fetch AtCoder stats for dashboard";
		};
		Service = {
			Type = "oneshot";
			ExecStart = "${pkgs.nix}/bin/nix-shell /home/treo/nixos-cp/dashboard/shell.nix --run 'python3 /home/treo/nixos-cp/dashboard/fetch_stats.py'";
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

	# Japanese input (fcitx5 + mozc)
	i18n.inputMethod = {
		enable = true;
		type = "fcitx5";
		fcitx5 = {
			waylandFrontend = true;
			addons = with pkgs; [
				fcitx5-mozc
				fcitx5-gtk
			];
		};
	};

	xdg.configFile."fcitx5/profile" = {
		force = true;
		text = ''
			[Groups/0]
			Name=Default
			Default Layout=us
			DefaultIM=keyboard-us

			[Groups/0/Items/0]
			Name=keyboard-us
			Layout=

			[Groups/0/Items/1]
			Name=mozc
			Layout=

			[GroupOrder]
			0=Default
		'';
	};

	programs.home-manager.enable = true;

	home.stateVersion = "24.11";
}

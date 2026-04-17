{ config, pkgs, lib, ... }:

{
	imports = [
		../../home/shell.nix
		../../home/git.nix
		../../home/starship.nix
		../../modules/sway.nix
		../../modules/nvim
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

	programs.home-manager.enable = true;

	home.stateVersion = "24.11";
}

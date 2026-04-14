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
		git
			htop
			wget
			curl
	];

	programs.home-manager.enable = true;

	home.stateVersion = "24.11";
}

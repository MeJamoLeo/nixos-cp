{
	description = "NixOS competitive programming workstation";

	inputs = {
		nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
		home-manager = {
			url = "github:nix-community/home-manager/release-24.11";
			inputs.nixpkgs.follows = "nixpkgs";
		};
		nixvim = {
			url = "github:nix-community/nixvim/nixos-24.11";
			inputs.nixpkgs.follows = "nixpkgs";
		};
		claude-code = {
			url = "github:sadjow/claude-code-nix";
			inputs.nixpkgs.follows = "nixpkgs";
		};
		zen-browser = {
			url = "github:0xc000022070/zen-browser-flake";
			inputs.nixpkgs.follows = "nixpkgs";
		};
		wayvibes = {
			url = "github:sahaj-b/wayvibes";
			inputs.nixpkgs.follows = "nixpkgs";
		};
	};

	outputs = { self, nixpkgs, home-manager, nixvim, claude-code, zen-browser, wayvibes, ... }: {
		nixosConfigurations = {
			# Dashboard + CLI tools only. Bring your own editor/browser.
			minimal = nixpkgs.lib.nixosSystem {
				system = "x86_64-linux";
				modules = [
					./hosts/minimal/configuration.nix
					home-manager.nixosModules.home-manager
					{
						home-manager.useGlobalPkgs = true;
						home-manager.useUserPackages = true;
						home-manager.users.treo = import ./profiles/minimal/home.nix;
					}
				];
			};

			# minimal + Neovim + Firefox + Sway + fcitx5
			full = nixpkgs.lib.nixosSystem {
				system = "x86_64-linux";
				modules = [
					./hosts/full/configuration.nix
					home-manager.nixosModules.home-manager
					{
						home-manager.useGlobalPkgs = true;
						home-manager.useUserPackages = true;
						home-manager.users.treo = import ./profiles/full/home.nix;
						home-manager.sharedModules = [
							nixvim.homeManagerModules.nixvim
						];
					}
				];
			};

			# full + X1 Carbon hardware, fingerprint, TLP, Claude Code
			x1nano = let system = "x86_64-linux"; in nixpkgs.lib.nixosSystem {
				inherit system;
				modules = [
					./hosts/x1nano/configuration.nix
					home-manager.nixosModules.home-manager
					{
						home-manager.useGlobalPkgs = true;
						home-manager.useUserPackages = true;
						home-manager.users.treo = import ./hosts/x1nano/home.nix;
						home-manager.sharedModules = [
							nixvim.homeManagerModules.nixvim
							wayvibes.nixosModules.default
						];
						home-manager.extraSpecialArgs = {
							claude-code-pkg = claude-code.packages.${system}.default;
							zen-browser-pkg = zen-browser.packages.${system}.default;
							wayvibes-soundpack = "${wayvibes}/soundpacks/nk-cream";
						};
					}
				];
			};
		};
	};
}

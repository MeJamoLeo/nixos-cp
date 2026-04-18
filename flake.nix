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
	};

	outputs = { self, nixpkgs, home-manager, nixvim, ... }: {
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

			# full + X1 Carbon hardware, fingerprint, TLP
			x1carbon = nixpkgs.lib.nixosSystem {
				system = "x86_64-linux";
				modules = [
					./hosts/x1carbon/configuration.nix
					home-manager.nixosModules.home-manager
					{
						home-manager.useGlobalPkgs = true;
						home-manager.useUserPackages = true;
						home-manager.users.treo = import ./hosts/x1carbon/home.nix;
						home-manager.sharedModules = [
							nixvim.homeManagerModules.nixvim
						];
					}
				];
			};
		};
	};
}

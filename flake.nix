{
	description = "NixOS configuration for X1 Carbon Nano as my single task dump laptop";

	inputs = {
		nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
		home-manager = {
			url = "github:nix-community/home-manager/release-24.11";
			inputs.nixpkgs.follows = "nixpkgs";
		};
	};

	outputs = { self, nixpkgs, home-manager, ... }: {
		nixosConfigurations.x1carbon = nixpkgs.lib.nixosSystem {
			system = "x86_64-linux";
			modules = [
				./hosts/x1carbon/configuration.nix
					home-manager.nixosModules.home-manager
					{
						home-manager.useGlobalPkgs = true;
						home-manager.useUserPackages = true;
						home-manager.users.treo = import ./hosts/x1carbon/home.nix;
					}
			];
		};
	};
}

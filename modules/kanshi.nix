{ config, pkgs, ... }:

{
	services.kanshi = {
		enable = false;
		systemdTarget = "sway-session.target";
		settings = [
			{
				profile.name = "docked";
				profile.outputs = [
					{
						criteria = "LG Electronics LG QHD 101KMGJY2775";
						mode = "2560x1440";
						position = "0,0";
					}
					{
						criteria = "eDP-1";
						status = "disable";
					}
				];
			}
			{
				profile.name = "undocked";
				profile.outputs = [
					{
						criteria = "eDP-1";
						status = "enable";
						position = "0,0";
					}
				];
			}
		];
	};
}

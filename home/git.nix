{ lib, ... }:

{
	home.activation.removeExistingGitconfig = lib.hm.dag.entryBefore ["checkLinkTargets"] ''
		rm -f ~/.gitconfig
		'';

	programs.git = {
		enable = true;
		lfs.enable = true;
		extraConfig = {
			user = {
				name = "MeJamoLeo";
				email = "55238651+MeJamoLeo@users.noreply.github.com";
			};
			init.defaultBranch = "main";
			push.autoSetupRemote = true;
			pull.rebase = true;
		};
		aliases = {
			br = "branch";
			co = "checkout";
			st = "status";
			cm = "commit -m";
			ca = "commit -am";
			dc = "diff --cached";
			amend = "commit --amend -m";
		};
		includes = [
		{
			path = "~/work/.gitconfig";
			condition = "gitdir:~/work/";
		}
		];
	};
}

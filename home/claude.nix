{ config, ... }:

# User-layer Claude Code skills, kept under version control in dotfiles/claude/skills.
# Live symlinks (mkOutOfStoreSymlink) so editing a SKILL.md in the repo takes effect
# immediately without nixos-rebuild — same pattern as cp/snippets.
#
# Bootstrap note: if ~/.claude/skills/<name> already exists as a real directory,
# home-manager will refuse to clobber it. Remove it once before the first switch:
#   rm -rf ~/.claude/skills/grill-me  # etc.

let
  skillsRepo = "${config.home.homeDirectory}/nixos-cp/dotfiles/claude/skills";
  link = name: {
    name = ".claude/skills/${name}";
    value.source = config.lib.file.mkOutOfStoreSymlink "${skillsRepo}/${name}";
  };
in
{
  home.file = builtins.listToAttrs (map link [
    "grill-me"
    "grill-with-docs"
    "domain-modeling"
  ]);
}

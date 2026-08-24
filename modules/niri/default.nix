{ config, pkgs, ... }:

{
  # niri's own default config, taken verbatim from niri 26.04 — the version in
  # nixpkgs 26.05, so the config and the binary agree.
  #
  # Deliberately NOT a translation of modules/sway.nix. niri is a scrolling
  # compositor rather than a tree, and its default binds assign the same keys
  # differently (Mod+Ctrl+HJKL moves a column; Mod+Shift+HJKL changes monitor —
  # sway uses those the other way round). Meeting it as designed first gives a
  # known baseline to diverge from, and keeps the wiki and community answers
  # applicable.
  #
  # `xdg.configFile` puts this in the store read-only: niri only reads its
  # config, never writes it, so this is fully declarative with no escape hatch
  # needed. That property is why niri is cheap to manage declaratively and
  # COSMIC is not — one KDL text file versus 73 RON files under ~/.config.
  xdg.configFile."niri/config.kdl".source = ./config.kdl;

  # The default config binds Mod+T to alacritty and Mod+D to fuzzel, and spawns
  # waybar at startup. None were installed. Without them the out-of-the-box
  # binds silently do nothing, which would not be "the default" in any useful
  # sense. swaylock, playerctl, brightnessctl and wpctl — also referenced by the
  # default binds — are already present.
  home.packages = with pkgs; [
    alacritty
    fuzzel
    waybar
  ];
}

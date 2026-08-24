{ config, pkgs, lib, claude-code-pkg, wayvibes-soundpack, ... }:

{
  imports = [
    ../../profiles/full/home.nix
  ];

  home.packages = [
    claude-code-pkg
    pkgs.obsidian
  ];

  # Zen: driven by the flake's home-manager module (imported in flake.nix as
  # zen-browser.homeModules.beta) instead of dropping the bare package into
  # home.packages. The module installs the wrapped package itself, so listing
  # it above as well would declare it twice.
  #
  # `profiles` is deliberately left unset. mkFirefoxModule only writes
  # profiles.ini when `profiles != {}` (home-manager
  # modules/programs/firefox/mkFirefoxModule.nix), so the existing
  # ~/.config/zen/<profile> — logins, cookies, history, per-extension settings
  # under browser-extension-data/ — survives untouched. Only the policy layer
  # (policies.json, regenerated from the store on every switch) is declarative.
  programs.zen-browser = {
    enable = true;

    # force_installed: the extension is installed and pinned by policy, and
    # cannot be removed from the UI. Slugs were resolved from the add-on GUIDs
    # via the AMO API rather than guessed — install_url depends on the slug and
    # a wrong one fails quietly.
    policies.ExtensionSettings =
      builtins.mapAttrs
        (_: slug: {
          install_url = "https://addons.mozilla.org/firefox/downloads/latest/${slug}/latest.xpi";
          installation_mode = "force_installed";
        })
        {
          "{d7742d87-e61d-4b78-b8a1-b469842139fa}" = "vimium-ff";
          "firefox@tampermonkey.net" = "tampermonkey";
          "{7be2ba16-0f1e-4d93-9ebc-5164397477a9}" = "videospeed";
          "myallychou@gmail.com" = "youtube-recommended-videos";
          "adguardadblocker@adguard.com" = "adguard-adblocker";
        };
  };

  services.wayvibes = {
    enable = true;
    soundpack = wayvibes-soundpack;
    volume = 5;
  };

  # CP snippets: symlink ~/cp/snippets → ~/nixos-cp/snippets so editing
  # the file in the repo is immediately picked up by LuaSnip without
  # going through the Nix store (no rebuild needed per snippet edit).
  home.file."cp/snippets".source =
    config.lib.file.mkOutOfStoreSymlink
      "${config.home.homeDirectory}/nixos-cp/snippets";
}

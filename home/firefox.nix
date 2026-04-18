{ config, pkgs, ... }:

{
  programs.firefox = {
    enable = true;
    profiles.default = {
      isDefault = true;
      search = {
        default = "DuckDuckGo";
        force = true;
      };
    };
  };
}

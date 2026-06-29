{ config, pkgs, ... }:

{
  imports = [
    ../minimal/configuration.nix
    ../../modules/cp-print.nix
  ];

  services.cp-print.enable = true;

  users.users.treo.extraGroups = [ "wheel" "networkmanager" "video" "input" ];

  environment.systemPackages = with pkgs; [
    brightnessctl
    pulseaudio
  ];

  # Auto-switch audio profile/port on jack events (headphones ↔ built-in speaker).
  # Without this, unplugging headphones leaves the card stuck on the Headphones
  # profile and Speaker sink disappears entirely.
  services.pipewire.wireplumber.extraConfig."51-alsa-autoswitch" = {
    "monitor.alsa.rules" = [{
      matches = [{ "device.name" = "~alsa_card.*"; }];
      actions.update-props = {
        "api.acp.auto-profile" = true;
        "api.acp.auto-port" = true;
      };
    }];
  };

  # Sway
  programs.sway.enable = true;

  # File manager (Thunar). gvfs gives trash + remote mounts; tumbler thumbnails.
  programs.thunar.enable = true;
  services.gvfs.enable = true;
  services.tumbler.enable = true;

  # Firefox: DuckDuckGo search, NoviSteps as homepage / startup page
  programs.firefox = {
    enable = true;
    policies = {
      SearchEngines = {
        Default = "DuckDuckGo";
      };
      Homepage = {
        URL = "https://novisteps.app/";
        StartPage = "homepage";
      };
    };
  };

  # Japanese input (fcitx5 + mozc)
  i18n.inputMethod = {
    enable = true;
    type = "fcitx5";
    fcitx5 = {
      waylandFrontend = true;
      addons = with pkgs; [
        fcitx5-mozc
        fcitx5-gtk
      ];
      settings = {
        inputMethod = {
          "Groups/0" = {
            Name = "Default";
            "Default Layout" = "us";
            DefaultIM = "mozc";
          };
          "Groups/0/Items/0" = {
            Name = "keyboard-us";
            Layout = "";
          };
          "Groups/0/Items/1" = {
            Name = "mozc";
            Layout = "";
          };
          GroupOrder = {
            "0" = "Default";
          };
        };
      };
    };
  };

  services.xserver.desktopManager.runXdgAutostartIfNone = true;

  # Suspend on lid close. Still suspend even when an external monitor is
  # attached — the dashboard is meant to be passive, not a reason to keep
  # the lid open. Power button stays on its default ("poweroff").
  services.logind = {
    lidSwitch = "suspend";
    lidSwitchExternalPower = "suspend";
    lidSwitchDocked = "suspend";
  };

  # Display manager
  services.greetd = {
    enable = true;
    settings = {
      default_session = {
        command = "${pkgs.greetd.tuigreet}/bin/tuigreet --cmd sway";
        user = "treo";
      };
    };
  };

  environment.sessionVariables = {
    WLR_NO_HARDWARE_CURSORS = "1";
    NIXOS_OZONE_WL = "1";
  };

  fonts.packages = with pkgs; [
    noto-fonts
    noto-fonts-cjk-sans
    noto-fonts-emoji
    (nerdfonts.override { fonts = [ "JetBrainsMono" ]; })
  ];

  fonts.fontconfig = {
    enable = true;
    antialias = true;
    hinting = {
      enable = true;
      style = "slight";
    };
    subpixel.lcdfilter = "light";
    defaultFonts.monospace = [ "JetBrainsMono Nerd Font" ];
  };
}

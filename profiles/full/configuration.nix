{ config, pkgs, ... }:

let
  # Which session tuigreet starts when you just hit enter. Follows whatever
  # compositor the host enables: hosts that turn on niri get niri, everything
  # else falls back to sway. Every session in --sessions is still reachable
  # from the picker (F3); this only decides the pre-filled one.
  defaultSessionCommand = if config.programs.niri.enable then "niri-session" else "sway";
in
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
    # base desktop (build check): COSMIC alongside sway; greeter picks the compositor
    services.desktopManager.cosmic.enable = true;

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
      ExtensionSettings = {
        "{d7742d87-e61d-4b78-b8a1-b469842139fa}" = {
          install_url = "https://addons.mozilla.org/firefox/downloads/latest/vimium-ff/latest.xpi";
          installation_mode = "force_installed";
        };
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

  # Always-on ssh box: never auto-suspend so x1nano stays reachable over ssh
  # even at the greeter (logged out) or with the lid closed on battery. A suspended
  # machine can't answer ssh (no reliable WoL over wifi), so we don't sleep at all.
  # Power button stays on its default ("poweroff").
  services.logind.settings.Login = {
    HandleLidSwitch = "ignore";
    HandleLidSwitchExternalPower = "ignore";
    HandleLidSwitchDocked = "ignore";
    IdleAction = "ignore";
  };

  # Hard-disable every sleep path so nothing (COSMIC / logind / systemd) can
  # suspend the machine and drop the ssh connection.
  systemd.targets = {
    sleep.enable = false;
    suspend.enable = false;
    hibernate.enable = false;
    hybrid-sleep.enable = false;
  };

  # Keep WiFi alive when the lid is closed so ssh stays reachable.
  networking.networkmanager.wifi.powersave = false;

  # Display manager
  services.greetd = {
    enable = true;
    settings = {
      default_session = {
        # --remember keeps the last username. --remember-session is deliberately
        # NOT used: it caches the last manual pick under /var/cache/tuigreet and
        # that cache overrides --cmd, so the declared default would lose to
        # whatever was clicked last. Dropping it keeps the default in the config
        # instead of in mutable state.
        command = "${pkgs.tuigreet}/bin/tuigreet --time --remember --cmd ${defaultSessionCommand} --sessions ${config.services.displayManager.sessionData.desktops}/share/wayland-sessions";
        user = "treo";
      };
    };
  };

  environment.sessionVariables = {
    WLR_NO_HARDWARE_CURSORS = "1";
    NIXOS_OZONE_WL = "1";
    TERMINAL = "kitty";  # single swap point if the terminal ever changes
    # Single source of truth for tmux's secure socket, so shells (via zsh init)
    # AND sway-spawned scripts (cp-go-launch etc.) hit the same server.
    # Without this, shells use $XDG_RUNTIME_DIR but scripts fall back to /tmp,
    # silently splitting into two parallel tmux universes.
    TMUX_TMPDIR = "$XDG_RUNTIME_DIR";
  };

  fonts.packages = with pkgs; [
    noto-fonts
    noto-fonts-cjk-sans
    noto-fonts-color-emoji
    nerd-fonts.jetbrains-mono
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

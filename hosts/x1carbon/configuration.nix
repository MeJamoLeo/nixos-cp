{ config, pkgs, ... }:

{
  imports = [
    ./hardware-configuration.nix
  ];

  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;

  networking.hostName = "x1carbon";
  networking.networkmanager.enable = true;

  time.timeZone = "America/Chicago";

  i18n.defaultLocale = "en_US.UTF-8";

  users.users.treo = {
    isNormalUser = true;
    extraGroups = [ "wheel" "networkmanager" "video" "input" ];
    shell = pkgs.zsh;
  };

  environment.systemPackages = with pkgs; [
    git
    vim
    wget
    curl
    kitty
    wofi
    brightnessctl
    pulseaudio
    python3
    online-judge-tools
    fzf
    wl-clipboard
  ];

  # SSH
  services.openssh.enable = true;

  # Fingerprint
  services.fprintd.enable = true;
  security.pam.services.login.fprintAuth = true;
  security.pam.services.sudo.fprintAuth = true;

  # CapsLock/Ctrl swap at TTY level
  console.useXkbConfig = true;
  services.xserver.xkb.options = "ctrl:swapcaps";

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

  # Sway needs XDG autostart for fcitx5
  services.xserver.desktopManager.runXdgAutostartIfNone = true;

  # TLP power management
  services.tlp.enable = true;

  # Sway
  programs.sway.enable = true;
  programs.zsh.enable = true;
  programs.firefox.enable = true;
  # programs.chromium.enable = true;
  # programs.qutebrowser.enable = true;

  # GNOMEの代わりにgreetd
  services.greetd = {
    enable = true;
    settings = {
      default_session = {
        command = "${pkgs.greetd.tuigreet}/bin/tuigreet --cmd sway";
        user = "treo";
      };
    };
  };

  # Wayland環境変数
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

  nix.settings.experimental-features = [ "nix-command" "flakes" ];

  system.stateVersion = "24.11";
}

{ config, pkgs, lib, ... }:

let
  # An action with no arguments. niri-flake represents an action as an attrset
  # with a single key (the action name) whose value is its argument list.
  act = name: { action.${name} = [ ]; };

  # An action with arguments. A single argument is implicitly wrapped in a list.
  act' = name: args: { action.${name} = args; };

  # Same key pressed with several modifier prefixes, all running the same action.
  # Used for the arrow/hjkl pairs that niri's default config binds identically.
  forKeys = keys: name: lib.genAttrs keys (_: act name);

  # Workspace 1..9: focus, and move the focused column there.
  workspaceBinds = lib.listToAttrs (
    lib.concatMap
      (n: [
        (lib.nameValuePair "Mod+${toString n}" (act' "focus-workspace" n))
        (lib.nameValuePair "Mod+Ctrl+${toString n}" (act' "move-column-to-workspace" n))
      ])
      (lib.range 1 9)
  );

  # allow-when-locked binds that shell out — the media and brightness keys.
  whenLocked = attrs: lib.mapAttrs (_: v: v // { allow-when-locked = true; }) attrs;
in
{
  # niri, configured through niri-flake's home-manager module rather than a raw
  # config.kdl. The settings below reproduce niri 26.04's shipped default config
  # exactly, plus the one local divergence (scale 1 on eDP-1).
  #
  # Version note: niri-flake's own niri-stable is 25.08 and its option types are
  # generated from that release's binds.rs, while the compositor here is nixpkgs'
  # niri 26.04. programs.niri.package is therefore pinned to pkgs.niri so the
  # build-time `niri validate` runs against the binary that will actually read
  # this config. Anything 26.04 added after 25.08 cannot be expressed until
  # niri-flake catches up; revisit then.
  programs.niri = {
    package = pkgs.niri;

    settings = {
      input = {
        keyboard.numlock = true;
        touchpad = {
          tap = true;
          natural-scroll = true;
        };
      };

      # The only deliberate divergence from upstream's defaults. The panel is
      # 2160x1350 over 280x170 mm (~196 PPI), so niri's automatic scale picks
      # 1.5; the sway config uses scale 1 on this same output and that is the
      # size these eyes are trained on.
      outputs."eDP-1".scale = 1;

      layout = {
        gaps = 16;
        center-focused-column = "never";
        preset-column-widths = [
          { proportion = 0.33333; }
          { proportion = 0.5; }
          { proportion = 0.66667; }
        ];
        default-column-width.proportion = 0.5;

        focus-ring = {
          width = 4;
          active.color = "#7fc8ff";
          inactive.color = "#505050";
        };

        border = {
          enable = false;
          width = 4;
          active.color = "#ffc87f";
          inactive.color = "#505050";
          urgent.color = "#9b0000";
        };

        shadow = {
          softness = 30;
          spread = 5;
          offset = { x = 0; y = 5; };
          color = "#0007";
        };
      };

      spawn-at-startup = [ { argv = [ "waybar" ]; } ];

      screenshot-path = "~/Pictures/Screenshots/Screenshot from %Y-%m-%d %H-%M-%S.png";

      window-rules = [
        {
          matches = [ { app-id = "^org\\.wezfurlong\\.wezterm$"; } ];
          default-column-width = { };
        }
        {
          matches = [
            {
              app-id = "firefox$";
              title = "^Picture-in-Picture$";
            }
          ];
          open-floating = true;
        }
      ];

      binds =
        {
          "Mod+Shift+Slash" = act "show-hotkey-overlay";

          # Programs. These are upstream's suggestions, not a considered choice:
          # niri ships no terminal, launcher or bar of its own, and the default
          # config just names common ones.
          "Mod+T" = (act' "spawn" "alacritty") // {
            hotkey-overlay.title = "Open a Terminal: alacritty";
          };
          "Mod+D" = (act' "spawn" "fuzzel") // {
            hotkey-overlay.title = "Run an Application: fuzzel";
          };
          "Super+Alt+L" = (act' "spawn" "swaylock") // {
            hotkey-overlay.title = "Lock the Screen: swaylock";
          };
          "Super+Alt+S" = (act' "spawn-sh" "pkill orca || exec orca") // {
            allow-when-locked = true;
            hotkey-overlay.hidden = true;
          };

          "Mod+O" = (act "toggle-overview") // { repeat = false; };
          "Mod+Q" = (act "close-window") // { repeat = false; };

          "Mod+Home" = act "focus-column-first";
          "Mod+End" = act "focus-column-last";
          "Mod+Ctrl+Home" = act "move-column-to-first";
          "Mod+Ctrl+End" = act "move-column-to-last";

          "Mod+BracketLeft" = act "consume-or-expel-window-left";
          "Mod+BracketRight" = act "consume-or-expel-window-right";
          "Mod+Comma" = act "consume-window-into-column";
          "Mod+Period" = act "expel-window-from-column";

          "Mod+R" = act "switch-preset-column-width";
          "Mod+Shift+R" = act "switch-preset-column-width-back";
          "Mod+Ctrl+Shift+R" = act "switch-preset-window-height";
          "Mod+Ctrl+R" = act "reset-window-height";

          "Mod+F" = act "maximize-column";
          "Mod+Shift+F" = act "fullscreen-window";
          "Mod+M" = act "maximize-window-to-edges";
          "Mod+Ctrl+F" = act "expand-column-to-available-width";
          "Mod+C" = act "center-column";
          "Mod+Ctrl+C" = act "center-visible-columns";

          "Mod+Minus" = act' "set-column-width" "-10%";
          "Mod+Equal" = act' "set-column-width" "+10%";
          "Mod+Shift+Minus" = act' "set-window-height" "-10%";
          "Mod+Shift+Equal" = act' "set-window-height" "+10%";

          "Mod+V" = act "toggle-window-floating";
          "Mod+Shift+V" = act "switch-focus-between-floating-and-tiling";
          "Mod+W" = act "toggle-column-tabbed-display";

          "Print" = act "screenshot";
          "Ctrl+Print" = act "screenshot-screen";
          "Alt+Print" = act "screenshot-window";

          "Mod+Escape" = (act "toggle-keyboard-shortcuts-inhibit") // {
            allow-inhibiting = false;
          };

          "Mod+Shift+E" = act "quit";
          "Ctrl+Alt+Delete" = act "quit";
          "Mod+Shift+P" = act "power-off-monitors";
        }

        # Arrow keys and hjkl are bound to the same actions throughout.
        // forKeys [ "Mod+Left" "Mod+H" ] "focus-column-left"
        // forKeys [ "Mod+Down" "Mod+J" ] "focus-window-down"
        // forKeys [ "Mod+Up" "Mod+K" ] "focus-window-up"
        // forKeys [ "Mod+Right" "Mod+L" ] "focus-column-right"

        // forKeys [ "Mod+Ctrl+Left" "Mod+Ctrl+H" ] "move-column-left"
        // forKeys [ "Mod+Ctrl+Down" "Mod+Ctrl+J" ] "move-window-down"
        // forKeys [ "Mod+Ctrl+Up" "Mod+Ctrl+K" ] "move-window-up"
        // forKeys [ "Mod+Ctrl+Right" "Mod+Ctrl+L" ] "move-column-right"

        // forKeys [ "Mod+Shift+Left" "Mod+Shift+H" ] "focus-monitor-left"
        // forKeys [ "Mod+Shift+Down" "Mod+Shift+J" ] "focus-monitor-down"
        // forKeys [ "Mod+Shift+Up" "Mod+Shift+K" ] "focus-monitor-up"
        // forKeys [ "Mod+Shift+Right" "Mod+Shift+L" ] "focus-monitor-right"

        // forKeys [ "Mod+Shift+Ctrl+Left" "Mod+Shift+Ctrl+H" ] "move-column-to-monitor-left"
        // forKeys [ "Mod+Shift+Ctrl+Down" "Mod+Shift+Ctrl+J" ] "move-column-to-monitor-down"
        // forKeys [ "Mod+Shift+Ctrl+Up" "Mod+Shift+Ctrl+K" ] "move-column-to-monitor-up"
        // forKeys [ "Mod+Shift+Ctrl+Right" "Mod+Shift+Ctrl+L" ] "move-column-to-monitor-right"

        // forKeys [ "Mod+Page_Down" "Mod+U" ] "focus-workspace-down"
        // forKeys [ "Mod+Page_Up" "Mod+I" ] "focus-workspace-up"
        // forKeys [ "Mod+Ctrl+Page_Down" "Mod+Ctrl+U" ] "move-column-to-workspace-down"
        // forKeys [ "Mod+Ctrl+Page_Up" "Mod+Ctrl+I" ] "move-column-to-workspace-up"
        // forKeys [ "Mod+Shift+Page_Down" "Mod+Shift+U" ] "move-workspace-down"
        // forKeys [ "Mod+Shift+Page_Up" "Mod+Shift+I" ] "move-workspace-up"

        // workspaceBinds

        # Mouse wheel. Rate-limited so a flick of the wheel does not tear
        # through several workspaces.
        // lib.mapAttrs (_: v: v // { cooldown-ms = 150; }) {
          "Mod+WheelScrollDown" = act "focus-workspace-down";
          "Mod+WheelScrollUp" = act "focus-workspace-up";
          "Mod+Ctrl+WheelScrollDown" = act "move-column-to-workspace-down";
          "Mod+Ctrl+WheelScrollUp" = act "move-column-to-workspace-up";
        }

        // {
          "Mod+WheelScrollRight" = act "focus-column-right";
          "Mod+WheelScrollLeft" = act "focus-column-left";
          "Mod+Ctrl+WheelScrollRight" = act "move-column-right";
          "Mod+Ctrl+WheelScrollLeft" = act "move-column-left";

          # Shift+wheel scrolls horizontally in most applications; mirror that.
          "Mod+Shift+WheelScrollDown" = act "focus-column-right";
          "Mod+Shift+WheelScrollUp" = act "focus-column-left";
          "Mod+Ctrl+Shift+WheelScrollDown" = act "move-column-right";
          "Mod+Ctrl+Shift+WheelScrollUp" = act "move-column-left";
        }

        # Media and brightness keys keep working while the session is locked.
        // whenLocked {
          "XF86AudioRaiseVolume" = act' "spawn-sh" "wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.1+ -l 1.0";
          "XF86AudioLowerVolume" = act' "spawn-sh" "wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.1-";
          "XF86AudioMute" = act' "spawn-sh" "wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle";
          "XF86AudioMicMute" = act' "spawn-sh" "wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle";
          "XF86AudioPlay" = act' "spawn-sh" "playerctl play-pause";
          "XF86AudioStop" = act' "spawn-sh" "playerctl stop";
          "XF86AudioPrev" = act' "spawn-sh" "playerctl previous";
          "XF86AudioNext" = act' "spawn-sh" "playerctl next";
          "XF86MonBrightnessUp" = act' "spawn" [ "brightnessctl" "--class=backlight" "set" "+10%" ];
          "XF86MonBrightnessDown" = act' "spawn" [ "brightnessctl" "--class=backlight" "set" "10%-" ];
        };
    };
  };

  # The default binds above name alacritty, fuzzel and waybar, none of which
  # were installed. Without them Mod+T and Mod+D silently do nothing, which
  # would not be "the default" in any useful sense. swaylock, playerctl,
  # brightnessctl and wpctl are already present.
  home.packages = with pkgs; [
    alacritty
    fuzzel
    waybar
  ];
}

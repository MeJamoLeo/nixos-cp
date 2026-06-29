{ config, pkgs, ... }:

{
  imports = [
    ../minimal/home.nix
    ../../home/starship.nix
    ../../home/kitty.nix
    ../../home/dashboard.nix
    ../../home/claude.nix
    ../../modules/sway.nix
    ../../modules/kanshi.nix
    ../../modules/nvim
  ];

  home.packages = with pkgs; [
    wofi
    wl-clipboard
    jq
    zed-editor
  ];

  programs.tmux = {
    enable = true;
    shortcut = "t";  # prefix = C-t (avoids vim <C-a>/<C-b> and cmp <C-Space>)
    keyMode = "vi";
    mouse = true;
    terminal = "tmux-256color";
    escapeTime = 0;
    baseIndex = 1;
    historyLimit = 10000;
    extraConfig = ''
      # TrueColor passthrough for kitty/foot/etc.
      set -ag terminal-overrides ",xterm-kitty:RGB,xterm-256color:RGB,foot:RGB"

      # nvim-like navigation:
      #   prefix + hjkl  → pane move (matches vim's <C-w>hjkl on splits)
      #   prefix + H/L   → window prev/next, repeatable (matches gT/gt feel)
      #   prefix + Tab   → last-window toggle (rescued from default `prefix l`)
      bind h select-pane -L
      bind j select-pane -D
      bind k select-pane -U
      bind l select-pane -R
      bind -r H previous-window
      bind -r L next-window
      bind Tab last-window
    '';
  };
}

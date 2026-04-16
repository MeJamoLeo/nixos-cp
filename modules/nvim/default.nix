{ pkgs, ... }:

{
  programs.nixvim = {
    enable = true;
    defaultEditor = true;

    opts = {
      number = true;
      relativenumber = true;
      shiftwidth = 4;
      tabstop = 4;
      expandtab = true;
      clipboard = "unnamedplus";
      undofile = true;
      ignorecase = true;
      smartcase = true;
      termguicolors = true;
      signcolumn = "yes";
      scrolloff = 8;
    };

    globals = {
      mapleader = " ";
    };

    # Treesitter
    plugins.treesitter = {
      enable = true;
      settings.ensure_installed = [
        "cpp"
        "python"
        "nix"
        "bash"
        "json"
        "markdown"
      ];
      settings.highlight.enable = true;
    };

    # LSP
    plugins.lsp = {
      enable = true;
      servers = {
        clangd = {
          enable = true;
          cmd = [ "clangd" "--background-index" "--clang-tidy" ];
        };
        pyright = {
          enable = true;
        };
      };
      keymaps = {
        lspBuf = {
          "gd" = "definition";
          "gD" = "declaration";
          "gr" = "references";
          "K" = "hover";
          "<leader>rn" = "rename";
          "<leader>ca" = "code_action";
        };
        diagnostic = {
          "[d" = "goto_prev";
          "]d" = "goto_next";
        };
      };
    };

    # Completion
    plugins.cmp = {
      enable = true;
      settings = {
        sources = [
          { name = "nvim_lsp"; }
          { name = "buffer"; }
          { name = "path"; }
        ];
        mapping = {
          "<C-n>" = "cmp.mapping.select_next_item()";
          "<C-p>" = "cmp.mapping.select_prev_item()";
          "<CR>" = "cmp.mapping.confirm({ select = true })";
          "<C-Space>" = "cmp.mapping.complete()";
        };
      };
    };

    # C++ / Python tooling
    extraPackages = with pkgs; [
      clang-tools  # clangd
      pyright
      gcc
      python3
    ];
  };
}

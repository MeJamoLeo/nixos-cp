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

    # File explorer
    plugins.oil = {
      enable = true;
      settings = {
        view_options.show_hidden = true;
      };
    };

    # Keybinding guide
    plugins.which-key = {
      enable = true;
      settings.spec = [
        { __unkeyed-1 = "<leader>c"; group = "Competitest"; }
        { __unkeyed-1 = "<leader>r"; group = "LSP Rename"; }
      ];
    };

    # Competitest (compile + run + test in nvim)
    plugins.competitest = {
      enable = true;
      settings = {
        save_current_file = true;
        compile_command = {
          cpp = {
            exec = "g++";
            args = ["-std=c++20" "-O2" "-Wall" "$(FNAME)" "-o" "$(FNOEXT)"];
          };
        };
        run_command = {
          cpp.exec = "./$(FNOEXT)";
          python = {
            exec = "python3";
            args = ["$(FNAME)"];
          };
        };
        runner_ui.interface = "popup";
        output_compare_method = "squish";
        maximum_time = 5000;
        # oj downloadのtest/ディレクトリに合わせる
        testcases_directory = "test";
        testcases_input_file_format = "sample-$(TCNUM).in";
        testcases_output_file_format = "sample-$(TCNUM).out";
      };
    };

    keymaps = [
      # File explorer
      { mode = "n"; key = "-"; action = "<cmd>Oil<cr>"; options.desc = "Open file explorer"; }

      # Competitest
      { mode = "n"; key = "<leader>cr"; action = "<cmd>CompetiTest run<cr>"; options.desc = "Run testcases"; }
      { mode = "n"; key = "<leader>cs"; action = "<cmd>w<cr><cmd>!cp-submit %<cr>"; options.desc = "Save + submit"; }
      { mode = "n"; key = "<leader>ca"; action = "<cmd>CompetiTest add_testcase<cr>"; options.desc = "Add testcase"; }
      { mode = "n"; key = "<leader>ce"; action = "<cmd>CompetiTest edit_testcase<cr>"; options.desc = "Edit testcase"; }
      { mode = "n"; key = "<leader>ct"; action = "<cmd>CompetiTest receive testcases<cr>"; options.desc = "Receive testcases"; }

      # Quick save/quit
      { mode = "n"; key = "<leader>w"; action = "<cmd>w<cr>"; options.desc = "Save"; }
      { mode = "n"; key = "<leader>q"; action = "<cmd>q<cr>"; options.desc = "Quit"; }
    ];

    # C++ / Python tooling
    extraPackages = with pkgs; [
      clang-tools  # clangd
      pyright
      gcc
      python3
    ];
  };
}

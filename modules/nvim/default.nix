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

    # Colorscheme
    colorschemes.tokyonight = {
      enable = true;
      settings.style = "night";
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

    # Snippets
    plugins.luasnip = {
      enable = true;
    };

    # Completion
    plugins.cmp = {
      enable = true;
      settings = {
        snippet.expand = ''function(args) require("luasnip").lsp_expand(args.body) end'';
        sources = [
          { name = "luasnip"; }
          { name = "nvim_lsp"; }
          { name = "buffer"; }
          { name = "path"; }
        ];
        mapping = {
          "<C-n>" = "cmp.mapping.select_next_item()";
          "<C-p>" = "cmp.mapping.select_prev_item()";
          "<CR>" = "cmp.mapping.confirm({ select = true })";
          "<C-Space>" = "cmp.mapping.complete()";
          "<Tab>" = ''cmp.mapping(function(fallback)
            local luasnip = require("luasnip")
            if luasnip.expand_or_jumpable() then luasnip.expand_or_jump()
            else fallback() end
          end, {"i", "s"})'';
          "<S-Tab>" = ''cmp.mapping(function(fallback)
            local luasnip = require("luasnip")
            if luasnip.jumpable(-1) then luasnip.jump(-1)
            else fallback() end
          end, {"i", "s"})'';
        };
      };
    };

    # Icons (Nerd Fonts)
    plugins.web-devicons.enable = true;

    # Auto pairs (括弧自動閉じ)
    plugins.nvim-autopairs.enable = true;

    # Status line
    plugins.lualine = {
      enable = true;
      settings.options.theme = "tokyonight";
    };

    # Comment toggle (gcc / gc)
    plugins.comment.enable = true;

    # Indentation guides
    plugins.indent-blankline.enable = true;

    # Git signs in gutter
    plugins.gitsigns.enable = true;

    # Fuzzy finder
    plugins.telescope = {
      enable = true;
      extensions.fzf-native.enable = true;
      settings = {
        defaults.vimgrep_arguments = [
          "${pkgs.ripgrep}/bin/rg"
          "--color=never"
          "--no-heading"
          "--with-filename"
          "--line-number"
          "--column"
          "--smart-case"
          "--hidden"
        ];
        pickers.find_files = {
          hidden = true;
        };
      };
    };

    # Keybinding guide
    plugins.which-key = {
      enable = true;
      settings.spec = [
        { __unkeyed-1 = "<leader>c"; group = "Competitest"; }
        { __unkeyed-1 = "<leader>f"; group = "Find"; }
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
      # Competitest
      { mode = "n"; key = "<leader>cr"; action = "<cmd>CompetiTest run<cr>"; options.desc = "Run testcases"; }
      # NOTE: cp-submit was removed. Bind <leader>cs to oj submit or competitest's
      # built-in submit when you decide on the new submit flow.
      { mode = "n"; key = "<leader>cs"; action = "<cmd>w<cr><cmd>!oj submit -y \"$(cat .problem_url)\" %<cr>"; options.desc = "Save + oj submit"; }
      { mode = "n"; key = "<leader>ca"; action = "<cmd>CompetiTest add_testcase<cr>"; options.desc = "Add testcase"; }
      { mode = "n"; key = "<leader>ce"; action = "<cmd>CompetiTest edit_testcase<cr>"; options.desc = "Edit testcase"; }
      { mode = "n"; key = "<leader>ct"; action = "<cmd>CompetiTest receive testcases<cr>"; options.desc = "Receive testcases"; }

      # Telescope
      { mode = "n"; key = "<leader>ff"; action = "<cmd>Telescope find_files<cr>"; options.desc = "Find files"; }
      { mode = "n"; key = "<leader>fg"; action = "<cmd>Telescope live_grep<cr>"; options.desc = "Live grep"; }
      { mode = "n"; key = "<leader>fb"; action = "<cmd>Telescope buffers<cr>"; options.desc = "Buffers"; }
      { mode = "n"; key = "<leader>fh"; action = "<cmd>Telescope help_tags<cr>"; options.desc = "Help"; }

      # Quick save/quit
      { mode = "n"; key = "<leader>w"; action = "<cmd>w<cr>"; options.desc = "Save"; }
      { mode = "n"; key = "<leader>q"; action = "<cmd>q<cr>"; options.desc = "Quit"; }
    ];

    # CP snippets: load .lua files from ~/cp/snippets/<filetype>.lua
    # so the user can `vim ~/cp/snippets/python.lua`, save, restart nvim,
    # and the new snippet is immediately available without rebuild.
    extraConfigLua = ''
      local ls = require("luasnip")
      local s = ls.snippet
      local t = ls.text_node
      local i = ls.insert_node

      require("luasnip.loaders.from_lua").lazy_load({
        paths = vim.fn.expand("~/cp/snippets"),
      })

      ls.add_snippets("markdown", {
        -- Inline math
        s("$", { t("$"), i(1), t("$") }),
        -- Display math
        s("$$", { t("$$"), i(1), t("$$") }),
        -- Common math
        s("On", { t("$O(n)$") }),
        s("Onlogn", { t("$O(n \\log n)$") }),
        s("On2", { t("$O(n^2)$") }),
        s("Ologn", { t("$O(\\log n)$") }),
        s("sum", { t("$\\sum_{"), i(1, "i=1"), t("}^{"), i(2, "n"), t("} "), i(3), t("$") }),
        s("frac", { t("$\\frac{"), i(1), t("}{"), i(2), t("}$") }),
        s("sqrt", { t("$\\sqrt{"), i(1), t("}$") }),
        s("leq", { t("$\\leq$") }),
        s("geq", { t("$\\geq$") }),
        s("neq", { t("$\\neq$") }),
        s("inf", { t("$\\infty$") }),
        s("floor", { t("$\\lfloor "), i(1), t(" \\rfloor$") }),
        s("ceil", { t("$\\lceil "), i(1), t(" \\rceil$") }),
        s("mod", { t("$"), i(1), t(" \\bmod "), i(2), t("$") }),
        s("arr", { t("$a_"), i(1, "i"), t("$") }),
        s("dp", { t("$dp["), i(1), t("]"), t("$") }),
      })
    '';

    # C++ / Python tooling
    extraPackages = with pkgs; [
      clang-tools  # clangd
      pyright
      gcc
      python3
      ripgrep  # telescope live_grep
    ];
  };
}

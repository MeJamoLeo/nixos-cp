{ pkgs, ... }:

let
  pythonWithDebugpy = pkgs.python3.withPackages (ps: [ ps.debugpy ]);

  # Wrapper used by the "CP debug" DAP config: opens test/sample-N.in as stdin
  # then runs the user's source file under debugpy so breakpoints fire normally.
  cpDebugRunner = pkgs.writeText "cp-debug-runner.py" ''
    import os, sys, runpy
    script, input_file = sys.argv[1], sys.argv[2]
    sys.stdin = open(input_file, "r")
    os.chdir(os.path.dirname(os.path.abspath(script)))
    sys.argv = [script]
    runpy.run_path(script, run_name="__main__")
  '';
in
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
          "<leader>la" = "code_action";
        };
        diagnostic = {
          "[d" = "goto_prev";
          "]d" = "goto_next";
        };
      };
    };

    # DAP (debugger)
    plugins.dap = {
      enable = true;
      extensions.dap-ui.enable = true;
      extensions.dap-python = {
        enable = true;
        adapterPythonPath = "${pythonWithDebugpy}/bin/python";
      };
      extensions.dap-virtual-text.enable = true;
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
        { __unkeyed-1 = "<leader>d"; group = "Debug"; }
        { __unkeyed-1 = "<leader>f"; group = "Find"; }
        { __unkeyed-1 = "<leader>l"; group = "LSP"; }
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
      { mode = "n"; key = "<leader>cs"; action = "<cmd>w<cr><cmd>!cp-submit %<cr>"; options.desc = "Save + submit"; }
      { mode = "n"; key = "<leader>ca"; action = "<cmd>CompetiTest add_testcase<cr>"; options.desc = "Add testcase"; }
      { mode = "n"; key = "<leader>ce"; action = "<cmd>CompetiTest edit_testcase<cr>"; options.desc = "Edit testcase"; }
      { mode = "n"; key = "<leader>ct"; action = "<cmd>CompetiTest receive testcases<cr>"; options.desc = "Receive testcases"; }
      { mode = "n"; key = "<leader>cd"; action = ''<cmd>lua require('dap').run(_G.cp_debug_config())<cr>''; options.desc = "CP debug (stdin = test/sample-N.in)"; }

      # Telescope
      { mode = "n"; key = "<leader>ff"; action = "<cmd>Telescope find_files<cr>"; options.desc = "Find files"; }
      { mode = "n"; key = "<leader>fg"; action = "<cmd>Telescope live_grep<cr>"; options.desc = "Live grep"; }
      { mode = "n"; key = "<leader>fb"; action = "<cmd>Telescope buffers<cr>"; options.desc = "Buffers"; }
      { mode = "n"; key = "<leader>fh"; action = "<cmd>Telescope help_tags<cr>"; options.desc = "Help"; }

      # Quick save/quit
      { mode = "n"; key = "<leader>w"; action = "<cmd>w<cr>"; options.desc = "Save"; }
      { mode = "n"; key = "<leader>q"; action = "<cmd>q<cr>"; options.desc = "Quit"; }

      # Debug (DAP) — all leader-based (no F-keys; laptop multimedia takes priority)
      { mode = "n"; key = "<leader>dc"; action = "<cmd>DapContinue<cr>"; options.desc = "Continue / start"; }
      { mode = "n"; key = "<leader>do"; action = "<cmd>DapStepOver<cr>"; options.desc = "Step over"; }
      { mode = "n"; key = "<leader>di"; action = "<cmd>DapStepInto<cr>"; options.desc = "Step into"; }
      { mode = "n"; key = "<leader>dO"; action = "<cmd>DapStepOut<cr>"; options.desc = "Step out"; }
      { mode = "n"; key = "<leader>db"; action = "<cmd>DapToggleBreakpoint<cr>"; options.desc = "Toggle breakpoint"; }
      { mode = "n"; key = "<leader>dB"; action = ''<cmd>lua require('dap').set_breakpoint(vim.fn.input('Condition: '))<cr>''; options.desc = "Conditional breakpoint"; }
      { mode = "n"; key = "<leader>dr"; action = "<cmd>DapToggleRepl<cr>"; options.desc = "Toggle REPL"; }
      { mode = "n"; key = "<leader>dx"; action = "<cmd>DapTerminate<cr>"; options.desc = "Terminate"; }
      { mode = "n"; key = "<leader>du"; action = ''<cmd>lua require('dapui').toggle()<cr>''; options.desc = "Toggle DAP UI"; }
      { mode = "n"; key = "<leader>dt"; action = ''<cmd>lua require('dap-python').test_method()<cr>''; options.desc = "Debug nearest test (Python)"; }
      { mode = "v"; key = "<leader>dn"; action = ''<cmd>lua require('dap-python').debug_selection()<cr>''; options.desc = "Debug selection (Python)"; }
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

      -- CP debug: build a DAP config that runs the current file under debugpy
      -- with test/sample-N.in piped to stdin (same testcase layout competitest uses).
      _G.cp_debug_config = function()
        local file = vim.fn.expand("%:p")
        local dir = vim.fn.expand("%:p:h")
        local tc = vim.fn.input("Testcase number: ", "1")
        if tc == "" then tc = "1" end
        local input_file = dir .. "/test/sample-" .. tc .. ".in"
        if vim.fn.filereadable(input_file) == 0 then
          vim.notify("Input file not found: " .. input_file, vim.log.levels.ERROR)
          return nil
        end
        return {
          type = "python",
          request = "launch",
          name = "CP: " .. vim.fn.fnamemodify(file, ":t") .. " < sample-" .. tc .. ".in",
          program = "${cpDebugRunner}",
          args = { file, input_file },
          cwd = dir,
          console = "integratedTerminal",
          justMyCode = false,
        }
      end
    '';

    # C++ / Python tooling
    extraPackages = with pkgs; [
      clang-tools  # clangd
      pyright
      gcc
      pythonWithDebugpy  # python3 + debugpy (DAP)
      ripgrep  # telescope live_grep
    ];
  };
}

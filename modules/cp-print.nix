{ config, lib, pkgs, ... }:

let
  cfg = config.services.cp-print;

  texEnv = pkgs.texlive.combine {
    inherit (pkgs.texlive)
      scheme-small
      collection-fontsrecommended
      collection-langjapanese
      collection-xetex
      xecjk
      fancyhdr
      geometry
      hyperref
      enumitem
      titlesec
      pgf
      eso-pic
      etoolbox
      anyfontsize
      ulem
      ;
  };

  py = pkgs.python3.withPackages (ps: with ps; [ beautifulsoup4 ]);
in
{
  options.services.cp-print = {
    enable = lib.mkEnableOption "cp-print AtCoder problem PDF builder";

    outputDir = lib.mkOption {
      type = lib.types.str;
      default = "$HOME/workspace/novisteps_prints";
      description = "Default output directory for generated PDFs.";
    };
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [
      texEnv
      py
      pkgs.pandoc
      pkgs.poppler_utils
      pkgs.qpdf
    ];

    # noto-fonts-cjk-sans ships as a variable-axis OTC which xdvipdfmx/luatex
    # can't embed (loca table not found). Pull in static Japanese fonts.
    fonts.packages = with pkgs; [
      ipaexfont
      dejavu_fonts
    ];

    environment.sessionVariables = {
      CP_PRINT_OUTPUT_DIR = cfg.outputDir;
    };
  };
}

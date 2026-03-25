{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  buildInputs = with pkgs; [
    cairo
    pango
    glib
    gdk-pixbuf
    fontconfig
    freetype
    python311
    nodejs_22
    jq
  ];

  LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
    pkgs.cairo
    pkgs.pango
    pkgs.glib
    pkgs.gdk-pixbuf
    pkgs.fontconfig
    pkgs.freetype
  ];
}

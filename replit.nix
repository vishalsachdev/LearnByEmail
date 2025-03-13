{pkgs}: {
  deps = [
    pkgs.sqlite-interactive
    pkgs.libxcrypt
    pkgs.rustc
    pkgs.libiconv
    pkgs.cargo
  ];
}

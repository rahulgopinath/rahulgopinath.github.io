#!/usr/bin/env nix-shell
#! nix-shell --pure --run "env i_fcolor=red zsh" .

let
  sysPkg = import <nixpkgs> { };
  pinnedPkg = sysPkg.fetchFromGitHub {
    owner = "NixOS";
    repo = "nixpkgs";
    rev = "16.09";
    sha256 = "1cx5cfsp4iiwq8921c15chn1mhjgzydvhdcmrvjmqzinxyz71bzh";
  };
  pkgs = import pinnedPkg {};
in with pkgs; stdenv.mkDerivation rec {

  name = "env";

  env = buildEnv {
    inherit name;
    paths = buildInputs;
  };

  jekyll_env = bundlerEnv rec {
     name = "jekyll_env";
     ruby = ruby_2_2;
     gemfile = ./Gemfile;
     lockfile = ./Gemfile.lock;
     gemset = ./gemset.nix;
  };


  builder = builtins.toFile "builder.sh" "source $stdenv/setup; ln -s $env $out";

  buildInputs = [
    ruby curl gitFull vim less jekyll_env
   ghostscript
  ];

  shellHook = ''
    export PS1="\[\e[33m\]|\[\e[m\] "
    TERM=xterm
    exec ${jekyll_env}/bin/jekyll serve --watch
  '';
}

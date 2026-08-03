{
  description = "BFD9020 development environment for model prediction";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05"; # or unstable
    treefmt-nix.url = "github:numtide/treefmt-nix";
    uv2nix.url = "github:pyproject-nix/uv2nix";
    pybuild.url = "github:pyproject-nix/build-system-pkgs";
    pyproject.url = "github:pyproject-nix/pyproject.nix";
  };

  outputs =
    { self, ... }@inputs:
    inputs.flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import inputs.nixpkgs { inherit system; };
        pkgs-treefmt = (import inputs.nixpkgs) {
          inherit system;
        };
        python = pkgs.python313;
        workspace = inputs.uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./src; };
        overlay = workspace.mkPyprojectOverlay {
          sourcePreference = "wheel";
        };
        uv2nixOverrides = final: prev: {
          torchaudio = prev.torchaudio.overrideAttrs (old: {
            # Let auto-patchelf scan inside the built torch package dependencies inside the sandbox
            preFixup = (old.preFixup or "") + ''
              addAutoPatchelfSearchPath ${final.torch}/${final.python.sitePackages}/torch/lib
            '';
          });
          torchvision = prev.torchvision.overrideAttrs (old: {
            # Let auto-patchelf scan inside the built torch package dependencies inside the sandbox
            preFixup = (old.preFixup or "") + ''
              addAutoPatchelfSearchPath ${final.torch}/${final.python.sitePackages}/torch/lib
            '';
          });
        };
        pythonBase = pkgs.callPackage inputs.pyproject.build.packages {
          inherit python;
        };
        pythonSet = pythonBase.overrideScope (
          pkgs.lib.composeManyExtensions [
            inputs.pybuild.overlays.wheel
            overlay
            uv2nixOverrides
          ]
        );
        venv = pythonSet.mkVirtualEnv "venv" workspace.deps.default;
        deps = [
        ];
        pako = pkgs.callPackage ./nix/pako.nix { };
        utif = pkgs.callPackage ./nix/utif.nix { };
        app = pkgs.callPackage ./nix/app.nix {
          inherit pako utif;
          pythonEnv = venv;
        };
        dockerImage = pkgs.callPackage ./nix/docker.nix {
          inherit deps;
          pythonEnv = venv;
          bfd9020-app = app;
        };
        load-podman = pkgs.callPackage ./nix/load-podman.nix { };
        treefmtconfig = inputs.treefmt-nix.lib.evalModule pkgs-treefmt {
          projectRootFile = "flake.nix";
          programs = {
            alejandra.enable = true;
            toml-sort.enable = true;
            yamlfmt.enable = true;
            mdformat = {
              enable = true;
              plugins = ps: [
                ps.mdformat-gfm
              ];
              settings = {
                wrap = 88;
                end-of-line = "lf";
              };
            };
            shellcheck.enable = true;
            shfmt.enable = true;
            nixfmt.enable = true;
          };
          settings.formatter.shellcheck.excludes = [
            ".envrc"
          ];
        };
      in
      {
        formatter = treefmtconfig.config.build.wrapper;
        devShells = {
          default = pkgs.mkShell {
            name = "fastapi-env";

            buildInputs =
              with pkgs;
              [
                watchman
                nil
                nixd
                uv
                ruff
                basedpyright
                podman
                podman-compose
                act
              ]
              ++ [
                venv
                load-podman
              ]
              ++ deps;

            env = {
              UV_NO_SYNC = "1";
              UV_PYTHON = pythonSet.python.interpreter;
              UV_PYTHON_DOWNLOADS = "never";
            };

            shellHook = ''
              PROJ_ROOT=$(git rev-parse --show-toplevel)/src
              export PYTHONPATH="$PROJ_ROOT:${venv}/lib/*/site-packages:$PYTHONPATH"
              ln -sfn ${venv} $PROJ_ROOT/.venv
            '';
          };
        };
        packages = {
          inherit
            dockerImage
            load-podman
            app
            ;
        };
        checks = {
          inherit dockerImage;
          formatting = treefmtconfig.config.build.check self;
          ruff-lint = pkgs.stdenvNoCC.mkDerivation {
            name = "ruff-lint";
            src = ./.;

            nativeBuildInputs = [ pkgs.ruff ];

            buildPhase = ''
              echo "Running Ruff linter checks..."
              ruff check ./src
            '';

            installPhase = "mkdir $out";
          };
          basedpyright-types = pkgs.stdenvNoCC.mkDerivation {
            name = "basedpyright-types";
            src = ./src;

            nativeBuildInputs = [
              venv
              pkgs.basedpyright
            ];

            buildPhase = ''
              echo "Running Basedpyright type checks..."
              ln -sfn ${venv} ./.venv
              basedpyright
            '';

            installPhase = "mkdir $out";
          };
        };
      }
    );
}

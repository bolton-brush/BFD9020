{
  dockerTools,
  pythonEnv,
  bfd9020-app,
  coreutils,
  bash,
  deps,
  ...
}:
dockerTools.buildLayeredImage {
  name = "bfd9020";
  tag = "build";

  contents = [
    pythonEnv
    bfd9020-app
    coreutils
    bash
  ]
  ++ deps;

  config = {
    # Drop root privileges completely
    User = "1000:1000";

    # Points directly to the initialization wrapper script below
    Cmd = [ "/share/bfd9020/entrypoint.sh" ];

    ExposedPorts = {
      "9020/tcp" = { };
    };

    Env = [
      "PYTHONUNBUFFERED=1"
    ];

    WorkingDir = "/share/bfd9020";
  };
}

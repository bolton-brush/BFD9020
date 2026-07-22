{
  stdenvNoCC,
  pythonEnv,
  pako,
  utif,
  openapi-python-client,
  python3,
  python3Packages,
  ...
}:
let
  app = stdenvNoCC.mkDerivation {
    name = "bfd9020";
    src = ../src;

    # Define multiple output targets
    outputs = [
      "out"
      "openapi"
    ];

    nativeBuildInputs = [ pythonEnv ];

    buildPhase = ''
      rm -r typings
    '';

    installPhase = ''
      # Primary application output ($out)
      mkdir -p $out/share/bfd9020
      cp -r * $out/share/bfd9020
      chmod +x $out/share/bfd9020/entrypoint.sh
      cp ${pako} $out/share/bfd9020/static/pako.min.js
      cp ${utif} $out/share/bfd9020/static/UTIF.js

      # Secondary openapi output ($openapi)
      mkdir -p $openapi
      python -c "import json; from main import app; print(json.dumps(app.openapi()))" > $openapi/openapi.json
    '';
  };
  client-sdk-src = stdenvNoCC.mkDerivation {
    name = "bfd9020-client-sdk";

    # Depends ONLY on openapi output, not the full app source
    src = app.openapi;

    nativeBuildInputs = [ openapi-python-client ];

    buildPhase = ''
      openapi-python-client generate --path $src/openapi.json --output-path sdk 2>&1 | tee build.log

      # Check for warnings in build log; fail if present
      if grep -i "warning" build.log; then
          echo "--------------------------------------------------------"
          echo "FAIL: openapi-python-client emitted warnings during build!"
          echo "--------------------------------------------------------"
          exit 1
      fi
    '';

    installPhase = ''
      mkdir -p $out
      cp -r sdk/{*,.gitignore} $out
    '';
  };
  clientSdkFunc =
    {
      buildPythonPackage,
      poetry-core,
      attrs,
      httpx,
      python-dateutil,
    }:
    buildPythonPackage {
      pname = "bfd9020-ai-api-client";
      version = "0.1.0";
      pyproject = true;

      src = client-sdk-src;

      build-system = [ poetry-core ];

      dependencies = [
        attrs
        httpx
        python-dateutil
      ];
    };
in
app.overrideAttrs (old: {
  passthru = (old.passthru or { }) // {
    client-sdk-func = clientSdkFunc;
    client-sdk = python3.pkgs.callPackage clientSdkFunc { };
    client-sdk-src = client-sdk-src;
    client-sdk-overlay = final: prev: {
      bfd9020-ai-api-client = final.callPackage clientSdkFunc {
        buildPythonPackage = final.buildPythonPackage or python3Packages.buildPythonPackage;
      };
    };
  };
})

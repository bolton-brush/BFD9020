# BFD9020

AI services backend for the BFD9000 project, starting with FastAPI-based image
classification.

## Models

All three models are ResNet-18 classifiers trained with FP16 and exported via FastAI.
They are loaded at startup and all three must be present for the service to run in a
fully healthy state (`/healthz` returns `"status": "ok"`).

| Model file                         | Key       | Role                                                                                    |
| ---------------------------------- | --------- | --------------------------------------------------------------------------------------- |
| `xtype-simple_resnet18_fp16_01`    | `xray`    | **X-ray type classifier** — coarse classification of the study (lateral, frontal, etc.) |
| `lateral_fliprot_resnet18_fp16_07` | `lateral` | **Lateral ceph orientation** — detects flip/rotation for lateral cephalometric images   |
| `frontal_fliprot_resnet18_fp16_03` | `frontal` | **Frontal ceph orientation** — detects flip/rotation for frontal cephalometric images   |

The `/xray-info` endpoint uses all three models in sequence: it first calls the `xray`
model to determine the study type, then — if the result is `lateral` or `frontal` —
calls the matching orientation model. The `/xray-class`, `/lateral-fliprot`, and
`/frontal-fliprot` endpoints each use one model independently.

## Repository Layout

```
src/                     # All application code
docker-compose.yml       # Development docker compose for quickly testing
.github/workflows/       # Tests and publication
flake.nix                # Repo toplevel, specifying the devshell, packages, tests, and formatter
```

## API

This FastAPI service exposes lightweight endpoints for both coarse X-ray typing and
flip/rotation inference on lateral and frontal ceph studies.

An `openapi.json` is provided at the `#app.openapi` flake URI or at `#app.client-sdk`
for a generated python sdk.

To build either of these artifacts, run `nix build .#app.openapi`

### Endpoints

- `GET /` – simple health/welcome message.
- `POST /xray-info` – returns type, rotation, and flip info for a single X-ray.
- `POST /xray-class` – predicts only the X-ray type.
- `POST /lateral-fliprot` – rotation/flip classification for lateral ceph images.
- `POST /frontal-fliprot` – rotation/flip classification for frontal ceph images.

## Utilities

- `BFD9020.html` – browser tester that runs all endpoints in sequence. When the API is
  running visit `/test`; otherwise open the file locally and point it to a remote base
  URL. TIFF previews are decoded client-side via vendored `pako` + `UTIF` scripts
  exposed from `/static`.

## Environment Variables

| Variable      | Default      | Description                                                     |
| ------------- | ------------ | --------------------------------------------------------------- |
| `LOG_LEVEL`   | `INFO`       | Python logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL)        |
| `ROOT_PATH`   | `""`         | FastAPI root path for reverse-proxy deployments                 |
| `ENABLE_DOCS` | `false`      | Set `true` to expose `/docs`, `/redoc`, `/openapi.json`         |
| `MODELS_DIR`  | `src/models` | Change this value if models are stored in a different directory |
| `ROOT_DOMAIN` | `::`         | Change this to set the CORS accepted domain header              |

Example with docs enabled:

```yaml
environment:
  LOG_LEVEL: "INFO"
  ROOT_PATH: "/bfd9020"
  ENABLE_DOCS: "true"
```

When deploying behind a reverse proxy (e.g., nginx proxy manager) with a path prefix
like `/bfd9020`, configure the proxy to strip the path before forwarding:

```nginx
location /bfd9020/ {
    rewrite ^/bfd9020(.*)$ $1 break;
    proxy_pass http://bfd9020:9020;
    proxy_redirect off;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Additionally, set the `ROOT_PATH` environment variable to inform FastAPI of its
deployment path. This ensures OpenAPI/Swagger UI generates correct URLs:

```yaml
environment:
  LOG_LEVEL: "INFO"
  ROOT_PATH: "/bfd9020"
```

When `ROOT_PATH` is set, FastAPI will correctly generate OpenAPI schemas and
documentation URLs that work through the proxy.

When developing for any application that requires a correct CORS context, ensure to set
the `ROOT_DOMAIN` environment variable. However, since this project should not have its
endpoints be public and instead be proxied by BFD9000, this should be a non-issue most
of the time.

## Running the Application with Nix

Running the application with nix is recommended for a consistent environment during
development. The project will run without nix, but will require additional setup and may
not be completely consistent with production if anything accidentally deviates from the
production build locally. It is recommended to always check the nix build and checks
work before merging a PR, although this will happen within CI as well.

```bash
nix develop
cd src

# Directly with uvicorn (models must be present locally)
uvicorn main:app --host "" --port 9020 --reload

# Or via the __main__ guard
python main.py

# Via Podman (recommended for CI/production)
podman-load
podman compose up
```

## Running the Application without Nix

```bash
# Ensure you have python 3.13 and uv installed locally first

cd src

uv venv
# Follow the instructions given by uv to activate the environment

# Directly with uvicorn (models must be present locally)
uvicorn main:app --host "" --port 9020 --reload

# Or via the __main__ guard
python main.py

# Building the docker image requires nix
```

If running without nix, the bfd9020 server will not have TIFF support by default.

To get TIFF support without nix, download pako and UTIF from the URLS provided in
`nix/pako.nix` and `nix/utif.nix` and place them within the `src/static` directory.

## Release Process (git-flow)

- Start a release branch from `develop`: `git flow release start vX.Y.Z` (use SemVer).
- Bump version in `config.py` to target version.
- Update release artifacts (docs, changelog) and ensure tests pass; no hard-coded
  version file exists, so choosing the new SemVer is enough.
- Finish the release to merge into `main` and back into `develop`:
  `git flow release finish vX.Y.Z`.
- Update the version on `develop` by bumping minor and adding `-dev` suffix.
- Push updated branches and the annotated tag: `git push origin main develop --tags`.
- Pushing the tag triggers the GHCR workflow, producing images tagged with the SemVer
  and branch/SHA variants.

Follow git-flow:

```bash
git flow release start vX.Y.Z
# bump changelog, verify endpoints
git flow release finish vX.Y.Z
git push origin main develop --tags
```

## Developing

- It is recommended to be within a `nix develop` shell or `direnv allow` in order to
  have the necessary dependencies to develop this project
- To build and load the docker image, run the `podman-load` command provided by the
  devshell before starting the `podman compose`.
- To add a package, either:
  - `uv add name_of_package`
  - Edit `pyproject.toml` and run `uv lock`

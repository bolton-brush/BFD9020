# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-08-17

### Added

- `MODELS_DIR` environment variable to configure the directory models are loaded from.
- `ROOT_DOMAIN` environment variable to set the CORS accepted domain header.
- Nix flake build system (`flake.nix`, `nix/`) providing the dev shell, application
  package, Docker image, and `podman-load` helper for streaming the image into Podman.
- Generated `openapi.json` and Python client SDK exposed as flake outputs
  (`#app.openapi`, `#app.client-sdk`).
- `converter/` — one-shot Docker tool converting legacy FastAI `.pkl` models into the
  ONNX + JSON sidecar format.
- GitHub Actions test workflow.
- Ruff configuration, `uv` lockfile, and vendored scikit-image type stubs.

### Changed

- **Breaking:** Inference migrated from FastAI pickled learners (`.pkl`) to ONNX
  Runtime; models now ship as `.onnx` files with `.json` sidecar metadata describing
  vocab and preprocessing.
- **Breaking:** Responses unified under a generic `ClassificationResult` schema
  (`prediction`, `probability`, `all_predictions`, `additional_info`):
  - `all_predictions` entries are now `{label, score}` objects instead of
    `[label, probability]` pairs.
  - `/xray-info` returns rotation/flip results under `additional_info` instead of the
    top-level `rotation`/`flip` fields.
  - `/lateral-fliprot` and `/frontal-fliprot` return `prediction` as a
    `{rotation, flip}` object instead of a raw orientation label.
  - `/xray-class` no longer includes the separate `code` field; `prediction` is the
    short code.
- Application restructured from a single `main.py` into a `src/` package (`main`,
  `config`, `classifier`, `model_manager`, `onnx_wrapper`, `image_utils`, `schemas`)
  with a central `ModelManager` handling model loading and caching.
- `/healthz` now reports per-model status and returns `degraded` when any model fails to
  load.
- Docker image is now built via Nix; the root `Dockerfile` and `.dockerignore` were
  removed.
- Maximum upload size increased from 10 MB to 50 MB.
- Version constant moved to `src/config.py`.

## [1.1.1] - 2026-03-03

### Changed

- `/xray-info` `type_prediction` now returns the canonical short code (e.g. `L`, `F`)
  instead of the long-form label, matching `/xray-class`.

## [1.1.0] - 2026-03-02

### Added

- Pydantic response models for all endpoints with OpenAPI documentation examples (fixes
  #5).
- X-ray type code mapping from long-form model labels to canonical short codes;
  `/xray-class` now returns short codes and includes a new `code` field.
- `VERSION` constant as the single source of the API version.
- `AGENTS.md` coding-agent guide.

### Fixed

- Corrected browser tester path to `static/BFD9020.html`.
- Flip/rotation mapping now accepts the lowercase `none` label produced by the model
  vocabulary.

## [1.0.1] - 2025-12-02

### Added

- `ROOT_PATH` environment variable for reverse proxy deployments (e.g., nginx proxy
  manager). Enables correct OpenAPI/Swagger URL generation when deployed at a path like
  `/bfd9020`.
- `ENABLE_DOCS` environment variable to control visibility of OpenAPI/Swagger
  documentation endpoints (`/docs`, `/redoc`, `/openapi.json`). Defaults to `false` for
  security.
- LICENSE file.

### Changed

- Updated FastAPI initialization to support dynamic docs and OpenAPI URL configuration
  based on `ENABLE_DOCS` environment variable.
- Removed files from docker image (README)
- Updated documentation with reverse proxy configuration examples and environment
  variable reference.

## [1.0.0] - 2025-12-02

### Added

- FastAPI service with X-ray classification endpoints (`/xray-info`, `/xray-class`,
  `/lateral-fliprot`, `/frontal-fliprot`).
- Browser-based endpoint tester (`BFD9020.html`).
- Dockerfile and docker-compose configuration for containerized deployment.
- GitHub Actions workflow to publish Docker images to GHCR on pushes to `main` and
  version tags.

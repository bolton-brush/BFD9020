# Dev Scratchpad

## Development environment

- It is recommended to be within a `nix develop` shell or `direnv allow` in order to
  have the necessary dependencies to develop this project
- To build and load the docker image, run the `podman-load` command provided by the
  devshell before starting the `podman compose`.

## Runtime overview

- Entry point `main.py` spins up FastAPI with `lifespan` that loads three fastai
  learners. Run by `python main.py` or `uvicorn main:app --host 0.0.0.0 --port 9020`.
- Async endpoints call FastAI `Learner.predict` via `run_in_threadpool`; uploads arrive
  as `UploadFile`.
- Upload guardrails: MIME whitelist (jpeg/png/tiff), 50 MB cap enforced via `seek` (no
  double read), centralized logging + exception hooks.
- `/healthz` reports readiness (`ok` vs `degraded`) based on which learners are loaded.

## API surface

- `/` welcome ping.
- `/xray-info` chained classification: global type + optional flip/rotation for
  lateral/frontal (uses `map_fliprot_prediction`).
- `/xray-class` type-only; `/lateral-fliprot` + `/frontal-fliprot` call
  `classify_specific_model` directly.
- All endpoints reuse `validate_file_size` + `validate_image`; responses include raw
  prediction, probability, full vocab w/ probabilities.

## Build & Dependency Management

- Be in the provided devshell (see README.md)
- To add a package, either:
  - `uv add name_of_package`
  - Edit `pyproject.toml` and run `uv lock`

Dependencies from the pyproject are automatically applied to the docker build with nix.

## Operational notes

- Logging now stdout-only (single `StreamHandler`), container-friendly.
- CORS wide open.
- Compose file (`docker-compose.yml`) builds from repo root, publishes `9020:9020`, sets
  `LOG_LEVEL=INFO`.
- Tester available at `/test` (serves `BFD9020.html`); standalone file also works
  locally. TIFF thumbnails are rendered via `<canvas>` using vendored pako and UTIF
  (FastAPI mounts `StaticFiles(directory="static")`).

# AGENTS.md — BFD9020 Coding Agent Guide

## Project Overview

FastAPI service that serves three FastAI image-classification learners for
X-ray cephalometric analysis. The entire backend lives in a single file
(`main.py`). There is no `requirements.txt` or `pyproject.toml`; all
dependencies are declared in the `Dockerfile`.

## Repository Layout

```
main.py                      # All application code
models/
  xtype-simple_resnet18_fp16_01        # X-ray type classifier
  lateral_fliprot_resnet18_fp16_07     # Lateral ceph flip/rotation classifier
  frontal_fliprot_resnet18_fp16_03     # Frontal ceph flip/rotation classifier
static/
  pako.min.js                # Vendored – do not modify
  UTIF.js                    # Vendored – do not modify
BFD9020.html                 # Browser endpoint tester (also served at /test)
Dockerfile                   # Multi-stage; python:3.13-slim base
docker-compose.yml
.github/workflows/publish-ghcr.yml
```

## Models

Three FastAI exported learners are loaded at startup:

| Key        | Path                                      | Purpose                                    |
|------------|-------------------------------------------|--------------------------------------------|
| `xray`     | `models/xtype-simple_resnet18_fp16_01`    | Coarse X-ray type classification           |
| `lateral`  | `models/lateral_fliprot_resnet18_fp16_07` | Flip/rotation inference for lateral ceph   |
| `frontal`  | `models/frontal_fliprot_resnet18_fp16_03` | Flip/rotation inference for frontal ceph   |

All three are ResNet-18 models trained with FP16 and exported via `fastai`'s
`export()`. They are committed as binary blobs (not Python packages). The
`label_func` stub in `main.py` exists solely to satisfy pickle deserialization.

## Running the Application

```bash
# Directly with uvicorn (models must be present locally)
uvicorn main:app --host 0.0.0.0 --port 9020 --reload

# Or via the __main__ guard
python main.py

# Via Docker (recommended for CI/production)
docker build -t bfd9020:test .
docker run --rm -p 9020:9020 bfd9020:test

# Via Compose
docker compose up --build
```

## Build & Dependency Management

There is no `pip install -r requirements.txt`. Dependencies are managed
exclusively through the `Dockerfile`. To add a dependency:

1. Add `pip install --no-cache-dir <pkg>` to the `base` stage in `Dockerfile`.
2. Import the package in `main.py` as needed.
3. Document the addition in `CHANGES.md`.

Current runtime dependencies (from `Dockerfile`):
- `torch`, `torchvision`, `torchaudio` (CPU wheels)
- `fastai<2.8`
- `scikit-image`
- `imageio`
- `fastapi[standard]` (includes `uvicorn`, `python-multipart`, etc.)
- `numpy` (pulled in transitively)

## Linting & Formatting

There is no enforced linter or formatter configuration in the repository.
Follow these conventions to match the existing code style:

- Use `flake8` or `ruff` locally if desired; no CI lint step exists yet.
- Line length: keep under ~100 characters where practical.
- Two blank lines between top-level definitions (PEP 8).
- One blank line between logically distinct blocks inside a function.
- Use `f-string` formatting for log messages only when the string is not
  passed to `logger.*` as a format argument; prefer `%`-style with `logger`
  calls (e.g., `logger.info("foo %s", bar)`) to avoid eager evaluation.

## Testing

There is no automated test suite at this time. Manual testing is done via:

```bash
# Browser tester (requires running API)
open http://localhost:9020/test

# Health probe
curl http://localhost:9020/healthz

# Classify a single image with curl
curl -X POST http://localhost:9020/xray-class \
     -F "image=@/path/to/image.jpg"

curl -X POST http://localhost:9020/lateral-fliprot \
     -F "image=@/path/to/lateral.tiff"

curl -X POST http://localhost:9020/frontal-fliprot \
     -F "image=@/path/to/frontal.png"

curl -X POST http://localhost:9020/xray-info \
     -F "image=@/path/to/image.jpg"
```

When adding tests in the future, use `pytest` with `httpx` and
`fastapi.testclient.TestClient`. A single test can be run with:

```bash
pytest tests/test_main.py::test_function_name -v
```

## Code Style Guidelines

### Imports

- Standard library imports first, then third-party, then local — each group
  separated by a blank line (PEP 8 / isort convention).
- No wildcard imports (`from module import *`).
- Prefer specific imports over blanket namespace imports where practical
  (e.g., `from fastai.vision.all import load_learner, PILImage`).

### Types & Annotations

- All public functions and async endpoints must have full type annotations on
  parameters and return types.
- Use `str`, `int`, `float`, `bool`, `dict`, `list` (built-in generics, Python
  3.10+ style) rather than `typing.Dict`, `typing.List`, etc.
- `UploadFile` parameters use FastAPI's `File(...)` default.

### Naming Conventions

- Functions and variables: `snake_case`.
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_IMAGE_SIZE`, `ALLOWED_MIME_TYPES`).
- FastAPI endpoint functions: descriptive verb-noun form
  (e.g., `classify_xray`, `get_xray_info`).
- Model dictionary keys: short lowercase strings (`"xray"`, `"lateral"`,
  `"frontal"`).

### Async Patterns

- All FastAPI endpoint handlers must be `async def`.
- CPU-bound FastAI inference calls (`Learner.predict`) must be wrapped in
  `run_in_threadpool` to avoid blocking the event loop.
- Helper functions called only from async endpoints should also be `async def`.
  Pure utility/mapping functions with no I/O may be synchronous.

### Error Handling

- Raise `HTTPException` for all user-visible errors with a clear `detail`
  string and an appropriate HTTP status code.
- Re-raise caught `HTTPException` instances directly (`raise he`).
- Catch broad `Exception` only at endpoint boundaries; log with
  `logger.exception(...)` (captures traceback) then raise a generic 500.
- Never swallow exceptions silently.

### Logging

- Use the module-level `logger = logging.getLogger(__name__)`.
- Entry into every public endpoint: `logger.info("<endpoint> endpoint called.")`.
- Preprocessing steps: `logger.debug(...)`.
- Successful predictions: `logger.info(...)` with class and probability.
- Unexpected model keys / unrecognized classes: `logger.warning(...)`.
- Errors: `logger.error(...)` for expected failure paths;
  `logger.exception(...)` (includes traceback) for unexpected exceptions.

### Docstrings

- Every public function and async endpoint must have a Google-style or
  reStructuredText-style docstring describing purpose, `Args`, `Returns`, and
  `Raises` where applicable.
- Inline comments should explain *why*, not restate *what* the code does.

## Environment Variables

| Variable      | Default   | Description                                              |
|---------------|-----------|----------------------------------------------------------|
| `LOG_LEVEL`   | `INFO`    | Python logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL) |
| `ROOT_PATH`   | `""`      | FastAPI root path for reverse-proxy deployments          |
| `ENABLE_DOCS` | `false`   | Set `true` to expose `/docs`, `/redoc`, `/openapi.json`  |

## Release Process

Follow git-flow:

```bash
git flow release start vX.Y.Z
# bump changelog, verify endpoints
git flow release finish vX.Y.Z
git push origin main develop --tags
```

Pushing an annotated `v*` tag triggers `.github/workflows/publish-ghcr.yml`,
which builds and pushes the Docker image to GHCR with `latest`, semver, and
SHA tags.

## Key Constraints & Gotchas

- **No test suite yet** — validate changes manually via `/test` and `curl`.
- **Models are binary blobs** — do not edit files under `models/`; replace
  them wholesale when retraining.
- **`label_func` stub** — must remain in `main.py` and registered on
  `sys.modules["__main__"]` or FastAI pickle deserialization will fail.
- **File pointer reset** — after reading an `UploadFile` for size validation,
  call `image.seek(0)` before any subsequent read or preprocessing.
- **CORS is wide open** — intentional for current deployment context; revisit
  before any public-facing exposure.
- **Docs disabled by default** — set `ENABLE_DOCS=true` only in development or
  trusted internal environments.

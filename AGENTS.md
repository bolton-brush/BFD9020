# AGENTS.md — BFD9020 Coding Agent Guide

## Project Overview

FastAPI service that serves three FastAI image-classification learners for X-ray
cephalometric analysis. The toplevel is the `flake.nix`, which specifies repo-wide
settings and `src/pyproject.toml` which specifies source-specific settings and
dependencies.

Read `README.md` and `src/README.md` for more information.

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

## Key Constraints & Gotchas

- **No test suite yet** — validate changes manually via `/test` and `curl`.
- **Models are binary blobs** — do not edit files under `src/models/`; replace them
  wholesale when retraining.
- **CORS is wide open** — intentional for current deployment context; revisit before any
  public-facing exposure.
- **Docs disabled by default** — set `ENABLE_DOCS=true` only in development or trusted
  internal environments.

# edu.case.BFD9020
AI services backend for the BFD9000 project, starting with FastAPI-based image classification.

## API

This FastAPI service exposes lightweight endpoints for both coarse X-ray typing and flip/rotation inference on lateral and frontal ceph studies.

### Endpoints

- `GET /` – simple health/welcome message.
- `POST /xray-info` – returns type, rotation, and flip info for a single X-ray.
- `POST /xray-class` – predicts only the X-ray type.
- `POST /lateral-fliprot` – rotation/flip classification for lateral ceph images.
- `POST /frontal-fliprot` – rotation/flip classification for frontal ceph images.

## Utilities

- `BFD9020.html` – browser tester that runs all endpoints in sequence. When the API is running visit `/test`; otherwise open the file locally and point it to a remote base URL. TIFF previews are decoded client-side via vendored `pako` + `UTIF` scripts exposed from `/static`.

## Local Docker Workflow

- Build the image standalone: `docker build -t bfd9020:test .` from the repo root.
- Run the container directly: `docker run --rm -p 9020:9020 bfd9020:test`.
- Or use the provided `docker-compose.yml` for a one-liner: `docker compose up --build` (press `Ctrl+C` to stop).
- Hit `http://localhost:9020` or open `BFD9020.html` and point it at the local API to verify endpoints.

## Release Process (git-flow)

- Start a release branch from `develop`: `git flow release start vX.Y.Z` (use SemVer).
- Update release artifacts (docs, changelog) and ensure tests pass; no hard-coded version file exists, so choosing the new SemVer is enough.
- Finish the release to merge into `main` and back into `develop`: `git flow release finish vX.Y.Z`.
- Push updated branches and the annotated tag: `git push origin main develop --tags`.
- Pushing the tag triggers the GHCR workflow, producing images tagged with the SemVer and branch/SHA variants.

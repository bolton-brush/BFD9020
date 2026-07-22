# Changelog

All notable changes to this project will be documented in this file.

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

# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-12-02

### Added

- FastAPI service with X-ray classification endpoints (`/xray-info`, `/xray-class`, `/lateral-fliprot`, `/frontal-fliprot`).
- Browser-based endpoint tester (`BFD9020.html`).
- Dockerfile and docker-compose configuration for containerized deployment.
- GitHub Actions workflow to publish Docker images to GHCR on pushes to `main` and version tags.

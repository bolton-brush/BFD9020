"""Application configuration settings."""

from __future__ import annotations

import os
from pathlib import Path

# Application
VERSION: str = "2.0.0"
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# Server & OpenAPI
ROOT_PATH: str = os.getenv("ROOT_PATH", "")
ENABLE_DOCS: bool = os.getenv("ENABLE_DOCS", "false").lower() == "true"
DOCS_URL: str | None = "/docs" if ENABLE_DOCS else None
REDOC_URL: str | None = "/redoc" if ENABLE_DOCS else None
OPENAPI_URL: str | None = "/openapi.json" if ENABLE_DOCS else None
ROOT_DOMAIN: str | None = os.getenv("ROOT_DOMAIN", None)

# File Upload Rules
ALLOWED_MIME_TYPES: list[str] = ["image/jpeg", "image/png", "image/tiff"]
MAX_IMAGE_SIZE: int = 50 * 1024 * 1024  # 50 MB

# Model Management
# Configurable models directory (Defaults to ./models)
SCRIPT_DIR = Path(__file__).resolve().parent
STATIC_DIR = SCRIPT_DIR / "static"
MODEL_DIR_FALLBACK = SCRIPT_DIR / "models"
MODELS_DIR: Path = Path(os.getenv("MODELS_DIR", None) or MODEL_DIR_FALLBACK)

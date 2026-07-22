"""Main FastAPI application server."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Annotated, Literal, TypedDict

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from classifier import (
    ACTIVE_CLASSIFIERS,
    FrontalClassifier,
    LateralClassifier,
    XrayClassifier,
)
from config import (
    DOCS_URL,
    LOG_LEVEL,
    MAX_IMAGE_SIZE,
    OPENAPI_URL,
    REDOC_URL,
    ROOT_DOMAIN,
    ROOT_PATH,
    STATIC_DIR,
    VERSION,
)
from image_utils import (
    validate_file_size,
    validate_image,
)
from model_manager import model_manager
from schemas import (
    ClassificationResult,
    FlipRot,
    XrayTypeCode,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# Logging configuration
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    """FastAPI lifespan manager to load models"""
    # Startup: Load ONNX models
    model_manager.warm_up(ACTIVE_CLASSIFIERS)
    yield  # noqa: RUF075
    logger.info("Shutting down application.")


app = FastAPI(
    title="BFD9020 AI API",
    description="API for high-performance X-ray classification.",
    version=VERSION,
    lifespan=lifespan,
    docs_url=DOCS_URL,
    redoc_url=REDOC_URL,
    openapi_url=OPENAPI_URL,
    root_path=ROOT_PATH,
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["localhost", ROOT_DOMAIN or "::"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Endpoints
@app.get("/test", include_in_schema=False)
async def serve_tester() -> FileResponse:
    """Serves the basic test site

    Returns:
        FileResponse of the static site

    """
    return FileResponse("static/BFD9020.html", media_type="text/html")


@app.get("/")
async def root() -> dict[str, str]:
    """Root GET message

    Returns:
        Simple welcome message

    """
    return {
        "message": "Welcome to the BFD9020 X-ray Classification API. "
        + "Visit /docs for API documentation."
    }


class HealthReturn(TypedDict):
    """Return type for healh check"""

    status: Literal["ok", "degraded"]
    models: dict[str, str]


@app.get("/healthz", include_in_schema=False)
async def healthz() -> HealthReturn:
    """Health check for the 9020 service, ensures all models are healthy

    Returns:
        Simple status formatted as a HealthReturn

    """
    statuses = [(model, model_manager.get_safe(model)) for model in ACTIVE_CLASSIFIERS]
    status = "ok" if all(s.is_ok() for _, s in statuses) else "degraded"
    errors = {
        m.name: "Errors: " + (s.map_err(str).err() or "none") for m, s in statuses
    }
    return {"status": status, "models": errors}


@app.post("/xray-class", response_model=ClassificationResult[XrayTypeCode, None])
async def classify_xray(
    image: Annotated[UploadFile, File()],
) -> ClassificationResult[XrayTypeCode, None]:
    """Classify an xray into its image type

    Args:
        image: The image to analyse

    Returns:
        A ClassificationResult object containing results of Xray Code type ("L"/"P"/...)

    """
    validate_file_size(image, MAX_IMAGE_SIZE)
    validate_image(image)
    im_bytes = await image.read()
    return model_manager.get(XrayClassifier).predict_and_preprocess(im_bytes)


@app.post("/lateral-fliprot", response_model=ClassificationResult[FlipRot, None])
async def classify_lateral_fliprot(
    image: Annotated[UploadFile, File()],
) -> ClassificationResult[FlipRot, None]:
    """Classify a lateral xray into its rotation type

    Args:
        image: The image to analyse

    Returns:
        A ClassificationResult object containing results of Flip + Rotation type

        Ex:
        ```
        {
            rotation: 0/90/180/270/None
            flip: True/False/None
        }
        ```

    """
    validate_file_size(image, MAX_IMAGE_SIZE)
    validate_image(image)
    im_bytes = await image.read()
    return model_manager.get(LateralClassifier).predict_and_preprocess(im_bytes)


@app.post("/frontal-fliprot", response_model=ClassificationResult[FlipRot, None])
async def classify_frontal_fliprot(
    image: Annotated[UploadFile, File()],
) -> ClassificationResult[FlipRot, None]:
    """Classify a frontal xray into its rotation type

    Args:
        image: The image to analyse

    Returns:
        A ClassificationResult object containing results of Flip + Rotation type

        Ex:
        ```
        {
            rotation: 0/90/180/270/None
            flip: True/False/None
        }
        ```

    """
    validate_file_size(image, MAX_IMAGE_SIZE)
    validate_image(image)
    im_bytes = await image.read()
    return model_manager.get(FrontalClassifier).predict_and_preprocess(im_bytes)


@app.post(
    "/xray-info",
    response_model=ClassificationResult[
        XrayTypeCode, ClassificationResult[FlipRot, None] | None
    ],
)
async def get_xray_info(
    image: Annotated[UploadFile, File()],
) -> ClassificationResult[XrayTypeCode, ClassificationResult[FlipRot, None] | None]:
    """Classify an xray into its image type and if applicable, rotation type

    Args:
        image: The image to analyse

    Returns:
        A ClassificationResult object containing results of Xray Code type,
        and if applicable, rotation info in the `additional_info` key.

        Only frontal or lateral images will have their rotation classified.

    """
    validate_file_size(image, MAX_IMAGE_SIZE)
    validate_image(image)
    im_bytes = await image.read()
    classifier = model_manager.get(XrayClassifier)
    tensor = classifier.preprocess(im_bytes)
    xray_res = classifier.predict(tensor)
    xray_class = xray_res.prediction

    match xray_class:
        case XrayTypeCode.F:
            model = model_manager.get(FrontalClassifier)
        case XrayTypeCode.L:
            model = model_manager.get(LateralClassifier)
        case _:
            return ClassificationResult[
                XrayTypeCode, ClassificationResult[FlipRot, None] | None
            ](
                prediction=xray_res.prediction,
                probability=xray_res.probability,
                all_predictions=xray_res.all_predictions,
                additional_info=None,
            )

    rot_class = model.predict(tensor)
    return ClassificationResult[
        XrayTypeCode, ClassificationResult[FlipRot, None] | None
    ](
        prediction=xray_res.prediction,
        probability=xray_res.probability,
        all_predictions=xray_res.all_predictions,
        additional_info=rot_class,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="", port=9020, reload=False)

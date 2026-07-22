"""Image preprocessing utilities using NumPy, PIL, and Scikit-Image."""

from __future__ import annotations

import io
import logging
import os

import imageio
import numpy as np
from fastapi import HTTPException, UploadFile
from result import as_result
from skimage import exposure
from skimage.transform import resize

from config import ALLOWED_MIME_TYPES

logger = logging.getLogger(__name__)

DEFAULT_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
DEFAULT_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def validate_file_size(image: UploadFile, max_size: int) -> None:
    """Validates that an uploaded file is below the maximum size

    Args:
        image: The uploaded file
        max_size: The maximum allowable size

    Raises:
        HTTPException: If file is too large

    """
    file_obj = image.file
    current_pos = file_obj.tell()
    _ = file_obj.seek(0, os.SEEK_END)
    image_size = file_obj.tell()
    _ = file_obj.seek(current_pos)

    if image_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"Image size exceeds maximum allowed size of {
                max_size / (1024 * 1024):.1f} MB.",
        )


def validate_image(image: UploadFile) -> None:
    """Validates that an image has an allowable MIME type

    Args:
        image: The uploaded file to check

    Raises:
        HTTPException: If an unsupported file type is present

    """
    if image.content_type not in ALLOWED_MIME_TYPES:
        logger.warning("Unsupported file type: %s", image.content_type)
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only JPEG, PNG, and TIFF are allowed.",
        )


@as_result(Exception)
def _load_preprocess_internal(
    image: bytes,
    target_size: tuple[int, int],  # (width, height)
    mean: np.ndarray,
    std: np.ndarray,
) -> np.ndarray:

    img = imageio.v3.imread(io.BytesIO(image))  # pyright: ignore[reportUnknownMemberType]

    # Handle Grayscale vs RGBA -> standard RGB (H, W, 3)
    if img.ndim == 2:  # noqa: PLR2004
        img = np.stack([img] * 3, axis=-1)
    elif img.ndim == 3 and img.shape[2] == 4:  # noqa: PLR2004
        img = img[..., :3]

    # 2. Rescale intensity to [0.0, 1.0] float32
    img_rescaled = exposure.rescale_intensity(
        img, in_range="image", out_range=(0.0, 1.0)
    ).astype(np.float32)

    # 3. Resize directly on floats (skimage resize expects (height, width))
    # Note: target_size is passed as (width, height), so we invert to (H, W)
    img_resized = resize(
        img_rescaled,
        (target_size[1], target_size[0]),
        order=1,
        preserve_range=True,
        anti_aliasing=True,
    )

    # 4. Standardize with broadcasted mean & std
    img_normalized = (img_resized - mean) / std

    # 5. Convert HWC -> CHW -> NCHW tensor
    tensor = np.transpose(img_normalized, (2, 0, 1))
    return np.expand_dims(tensor, axis=0).astype(np.float32)


def load_and_preprocess_image(
    image: bytes,
    target_size: tuple[int, int] = (299, 299),  # (width, height)
    mean: np.ndarray | None = None,
    std: np.ndarray | None = None,
) -> np.ndarray:
    """Loads, standardizes, and scales an image for the model

    Args:
        image: The uploaded file to process
        target_size: The size to rescale to
        mean: The mean for values within this image
        std: The STD for values within this image

    Returns:
        An ndarray with the image data

    Raises:
        HTTPException: If anything fails to process

    """
    mean_val = mean if mean is not None else DEFAULT_MEAN
    std_val = std if std is not None else DEFAULT_STD

    res = _load_preprocess_internal(image, target_size, mean_val, std_val)
    if res.is_err():
        logger.exception("Failed to load and preprocess image: %s", res.err())
        raise HTTPException(status_code=400, detail="Invalid image data.")

    return res.unwrap()

"""ONNX Model Manager reading parameters dynamically from sidecar metadata."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from result import Result, as_result

from config import MODELS_DIR

if TYPE_CHECKING:
    from pathlib import Path

    from onnx_wrapper import Classifier, ONNXModelWrapper

logger = logging.getLogger(__name__)


class ModelManager:
    """Central manager providing once-locked model instances"""

    def __init__(self, models_dir: Path) -> None:
        """Initialize the model manager with a model directory"""
        self.models_dir: Path = models_dir

    def get[T, U](
        self, classifier_cls: type[Classifier[T, U]]
    ) -> ONNXModelWrapper[T, U]:
        """Fetches an ONNXModelWrapper instance.

        Loads and constructs the ONNX runtime session on the first call,
        and returns the cached instance on all subsequent calls.

        Args:
            classifier_cls: Either a Classifier instance (e.g. `XrayClassifier()`)
                or class reference (e.g. `XrayClassifier`).

        Returns:
            The once-locked ONNXModelWrapper typed to T and U.

        """
        # Resolve class to an instance if a class reference was passed
        return classifier_cls.get_model(self.models_dir)

    def get_safe[T, U](
        self, classifier_cls: type[Classifier[T, U]]
    ) -> Result[ONNXModelWrapper[T, U], Exception]:
        """Fetches an ONNXModelWrapper instance.

        Loads and constructs the ONNX runtime session on the first call,
        and returns the cached instance on all subsequent calls.

        Args:
            classifier_cls: Either a Classifier instance (e.g. `XrayClassifier()`)
                or class reference (e.g. `XrayClassifier`).

        Returns:
            The once-locked ONNXModelWrapper typed to T and U.

        """
        # Resolve class to an instance if a class reference was passed
        return as_result(Exception)(classifier_cls.get_model)(self.models_dir)

    def warm_up(
        self,
        classifiers: list[type[Classifier[Any, Any]]],  # pyright: ignore[reportExplicitAny]
    ) -> None:
        """Loads and once-locks specified models into RAM ahead of time"""
        for item in classifiers:
            _ = self.get(item)


# Global instance
model_manager = ModelManager(MODELS_DIR)

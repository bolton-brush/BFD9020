"""ONNX Model Wrapper for our Classifier Types"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from functools import cache
from typing import TYPE_CHECKING, Any

import numpy as np
import onnxruntime as ort
from pydantic import BaseModel, Field, model_validator

from image_utils import load_and_preprocess_image
from schemas import ClassificationResult, PredictionScore

if TYPE_CHECKING:
    from pathlib import Path


class Classifier[T, U](ABC):
    """Base Classifier configuration and associated types."""

    ReturnType: type[T]
    MappedType: type[U]

    name: str
    path: str

    @classmethod
    @abstractmethod
    def map_output(cls, label: T) -> U:
        """Maps the model type to our output type

        Args:
            label: The input T type

        Returns:
            The mapped U type

        """
        ...

    @classmethod
    def get_model(cls, models_dir: Path) -> ONNXModelWrapper[T, U]:
        """Load the ONNX runtime from for this classifier

        Args:
            models_dir: The path to the model files

        Returns:
            The ONNX Wrapper for this classifier

        """
        """Factory method to load the model (uses thread-safe cache under the hood)."""
        return _get_cached_model(cls, models_dir)


@cache
def _get_cached_model[T, U](
    classifier_cls: type[Classifier[T, U]], models_dir: Path
) -> ONNXModelWrapper[T, U]:
    """Internal function that instantiates ONNXModelWrapper exactly ONCE per class.

    Args:
        classifier_cls: Which classifier to load
        models_dir: The path to the model files

    Returns:
        The ONNX Wrapper for this classifier

    """
    return ONNXModelWrapper(classifier_cls, models_dir)


class JSONSidecar[LabelT](BaseModel):
    """The type of the model sidecar info"""

    vocab: list[LabelT] = Field(default_factory=list)
    # Target 1D float lists for clean downstream use
    mean: list[float] = Field(default_factory=lambda: [0.485, 0.456, 0.406])
    std: list[float] = Field(default_factory=lambda: [0.229, 0.224, 0.225])
    input_size: tuple[int, int] = Field(default_factory=lambda: (224, 224))

    @model_validator(mode="before")
    @classmethod
    def _normalize_stats_before(cls, data: Any) -> Any:  # pyright: ignore[reportExplicitAny, reportAny]  # noqa: ANN401
        if isinstance(data, dict):
            for field in ("mean", "std"):
                if field in data and isinstance(data[field], list):
                    arr = np.asarray(data[field], dtype=np.float32).squeeze()  # pyright: ignore[reportUnknownArgumentType]
                    data[field] = arr.tolist()
        return data  # pyright: ignore[reportUnknownVariableType]


class ONNXModelWrapper[T, U]:
    """An ONNX Model runner parameterized directly by a Classifier specification."""

    session: ort.InferenceSession
    input_name: str
    metadata: JSONSidecar[T]
    Classifier: type[Classifier[T, U]]

    def __init__(
        self, classifier_cls: type[Classifier[T, U]], models_dir: Path
    ) -> None:
        """Create ONNX model runner from a Classifier definition and models directory.

        Args:
            classifier_cls: The type of the classifier to instance
            models_dir: The path to the model files

        Raises:
            FileNotFoundError: If the model ONNX or JSON files are not found

        """
        self.Classifier = classifier_cls
        onnx_file = models_dir / f"{classifier_cls.path}.onnx"
        json_file = models_dir / f"{classifier_cls.path}.json"

        if not onnx_file.exists() or not json_file.exists():
            raise FileNotFoundError(
                f"Missing ONNX/JSON model files for classifier '{
                    classifier_cls.name
                }' at '{onnx_file}'"
            )

        # ONNX Runtime Session setup
        opts = ort.SessionOptions()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL  # pyright: ignore[reportUnknownMemberType]
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL  # pyright: ignore[reportUnknownMemberType]

        self.session = ort.InferenceSession(
            str(onnx_file),
            providers=["CPUExecutionProvider"],
            sess_options=opts,  # pyright: ignore[reportUnknownArgumentType]
        )
        self.input_name = self.session.get_inputs()[0].name  # pyright: ignore[reportUnknownMemberType]

        # Load Metadata JSON using the associated ReturnType Enum (T)
        with json_file.open("r", encoding="utf-8") as f:
            self.metadata = JSONSidecar[T].model_validate(json.load(f))

    def preprocess(
        self,
        image: bytes,
    ) -> np.ndarray:
        """Helper to invoke the external preprocessor using sidecar metadata.

        Args:
            image: The bytes for the image to preprocess

        Returns:
            The preprocess np.ndarray for passing into a model

        """
        return load_and_preprocess_image(
            image,
            target_size=self.metadata.input_size,
            mean=np.array(self.metadata.mean, dtype=np.float32),
            std=np.array(self.metadata.std, dtype=np.float32),
        )

    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return e_x / e_x.sum(axis=-1, keepdims=True)

    def predict(self, input_tensor: np.ndarray) -> ClassificationResult[U, None]:
        """Predicts upon a given input tensor.

        Returns:
            The top class Enum instance (T), top index,
            and list of probabilities per class.

        """
        outputs = self.session.run(None, {self.input_name: input_tensor})  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        logits: np.ndarray = outputs[0][0]  # pyright: ignore[reportIndexIssue, reportUnknownVariableType]
        probs: list[float] = self._softmax(logits).tolist()  # pyright: ignore[reportUnknownArgumentType, reportAny]

        top_idx = int(np.argmax(probs))
        probs_list: list[PredictionScore[U]] = [
            PredictionScore[U](label=self.Classifier.map_output(cls), score=float(prob))
            for cls, prob in zip(self.metadata.vocab, probs, strict=True)
        ]

        return ClassificationResult[U, None](
            prediction=probs_list[top_idx].label,
            probability=probs_list[top_idx].score,
            all_predictions=probs_list,
            additional_info=None,
        )

    def predict_and_preprocess(self, image: bytes) -> ClassificationResult[U, None]:
        """Predicts upon a given image.

        Returns:
            The top class Enum instance (T), top index,
            and list of probabilities per class.

        """
        input_tensor = self.preprocess(image)
        return self.predict(input_tensor)

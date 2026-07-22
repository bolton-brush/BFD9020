"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Annotated, TypedDict

from pydantic import BaseModel, Field


class XrayTypeLabel(StrEnum):
    """Xray labels returned from models"""

    CHEST_SHOULDER = "Chest & Shoulder"
    ELBOW = "Elbow"
    FOOT_ANKLE = "Foot & Ankle"
    FRONTAL = "Frontal"
    HAND_WRIST = "Hand & Wrist"
    HIP_PELVIS = "Hip & Pelvis"
    KNEE = "Knee"
    LATERAL = "Lateral"


class XrayTypeCode(StrEnum):
    """Xray label codes"""

    CS = "CS"
    E = "E"
    FA = "FA"
    F = "F"
    H = "H"
    P = "P"
    K = "K"
    L = "L"


class FlipRotLabel(StrEnum):
    """Rotation labels returned from models"""

    R0 = "0"
    R0F = "0F"
    R90 = "90"
    R90F = "90F"
    R180 = "180"
    R180F = "180F"
    R270 = "270"
    R270F = "270F"
    NONE = "none"


class FlipRotAngle(IntEnum):
    """Valid rotation angles"""

    A0 = 0
    A90 = 90
    A180 = 180
    A270 = 270


class FlipRot(TypedDict):
    """Rotation and Flip dictionary"""

    rotation: FlipRotAngle | None
    flip: bool | None


@dataclass
class PredictionScore[LabelT]:
    """A prediction label paired with a score"""

    label: LabelT
    score: Annotated[float, Field(ge=0.0, le=1.0)]


class ClassificationResult[LabelT, Additional](BaseModel):
    """Base generic payload for single-head model predictions."""

    prediction: LabelT = Field(description="Predicted class label for top prediction.")
    probability: float = Field(
        ge=0.0, le=1.0, description="Confidence score for top prediction."
    )
    all_predictions: list[PredictionScore[LabelT]] = Field(
        description="Full label vocabulary paired with confidence probabilities.",
    )
    additional_info: Additional = Field(
        description="Additional Information added to this response"
    )

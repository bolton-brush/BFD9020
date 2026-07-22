"""Classifier Configuration"""

from __future__ import annotations

from typing import Any, final, override

from onnx_wrapper import Classifier
from schemas import FlipRot, FlipRotAngle, FlipRotLabel, XrayTypeCode, XrayTypeLabel

# ============================================================================
# Classifiers Definition
# ============================================================================


@final
class XrayClassifier(Classifier[XrayTypeLabel, XrayTypeCode]):
    """Xray Classifier model"""

    ReturnType = XrayTypeLabel
    MappedType = XrayTypeCode

    name = "xray"
    path = "xtype-simple_resnet18_fp16_01"

    @override
    @classmethod
    def map_output(cls, label: XrayTypeLabel) -> XrayTypeCode:
        return XRAY_TYPE_CODE[label]


@final
class LateralClassifier(Classifier[FlipRotLabel, FlipRot]):
    """Lateral Image Rotation model"""

    ReturnType = FlipRotLabel
    MappedType = FlipRot

    name = "lateral"
    path = "lateral_fliprot_resnet18_fp16_07"

    @override
    @classmethod
    def map_output(cls, label: FlipRotLabel) -> FlipRot:
        return FLIPROT_MAPPING[label]


@final
class FrontalClassifier(Classifier[FlipRotLabel, FlipRot]):
    """Frontal Image Rotation model"""

    ReturnType = FlipRotLabel
    MappedType = FlipRot

    name = "frontal"
    path = "frontal_fliprot_resnet18_fp16_03"

    @override
    @classmethod
    def map_output(cls, label: FlipRotLabel) -> FlipRot:
        return FLIPROT_MAPPING[label]


# ============================================================================
# Dict Mappings
# ============================================================================

XRAY_TYPE_CODE: dict[XrayTypeLabel, XrayTypeCode] = {
    XrayTypeLabel.CHEST_SHOULDER: XrayTypeCode.CS,
    XrayTypeLabel.ELBOW: XrayTypeCode.E,
    XrayTypeLabel.FOOT_ANKLE: XrayTypeCode.FA,
    XrayTypeLabel.FRONTAL: XrayTypeCode.F,
    XrayTypeLabel.HAND_WRIST: XrayTypeCode.H,
    XrayTypeLabel.HIP_PELVIS: XrayTypeCode.P,
    XrayTypeLabel.KNEE: XrayTypeCode.K,
    XrayTypeLabel.LATERAL: XrayTypeCode.L,
}


FLIPROT_MAPPING: dict[FlipRotLabel, FlipRot] = {
    FlipRotLabel.R0: {"rotation": FlipRotAngle.A0, "flip": False},
    FlipRotLabel.R0F: {"rotation": FlipRotAngle.A0, "flip": True},
    FlipRotLabel.R90: {"rotation": FlipRotAngle.A90, "flip": False},
    FlipRotLabel.R90F: {"rotation": FlipRotAngle.A90, "flip": True},
    FlipRotLabel.R180: {"rotation": FlipRotAngle.A180, "flip": False},
    FlipRotLabel.R180F: {"rotation": FlipRotAngle.A180, "flip": True},
    FlipRotLabel.R270: {"rotation": FlipRotAngle.A270, "flip": False},
    FlipRotLabel.R270F: {"rotation": FlipRotAngle.A270, "flip": True},
    FlipRotLabel.NONE: {"rotation": None, "flip": None},
}

ACTIVE_CLASSIFIERS: list[type[Classifier[Any, Any]]] = [  # pyright: ignore[reportExplicitAny]
    XrayClassifier,
    LateralClassifier,
    FrontalClassifier,
]

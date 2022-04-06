from enum import Enum


class ImageInfo(Enum):
    MIN = "min"
    MAX = "max"
    MEAN = "mean"


class MorphoOperation(Enum):
    EROSION = "erosion"
    DILATION = "dilation"
    OPENING = "opening"
    CLOSING = "closing"


class MathOperation(Enum):
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"

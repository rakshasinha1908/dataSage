from dataclasses import dataclass
from typing import Any

from models.visualization import Visualization


@dataclass
class Response:

    success: bool

    answer: Any

    visualization: Visualization | None

    error: str | None = None
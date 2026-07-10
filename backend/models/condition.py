from dataclasses import dataclass
from typing import Any


@dataclass
class Condition:
    """
    Represents a single filtering condition.
    """

    column: str

    operator: str

    value: Any
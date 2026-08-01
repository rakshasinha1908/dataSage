from dataclasses import dataclass
from models.condition import Condition


@dataclass
class NumericFilterParseResult:
    conditions: list[Condition]
    cleaned_text: str
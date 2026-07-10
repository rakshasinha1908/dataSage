from dataclasses import dataclass, field
from typing import List

from models.condition import Condition


@dataclass
class ConditionParseResult:
    """
    Output produced by the ConditionParser.
    """

    cleaned_text: str

    conditions: List[Condition] = field(default_factory=list)
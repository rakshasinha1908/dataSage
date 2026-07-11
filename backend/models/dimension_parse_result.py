from dataclasses import dataclass, field
from typing import List

from models.dimension import Dimension


@dataclass
class DimensionParseResult:
    """
    Output produced by the DimensionParser.
    """

    cleaned_text: str

    dimensions: List[Dimension] = field(default_factory=list)
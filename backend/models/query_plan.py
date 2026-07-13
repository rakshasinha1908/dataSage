from dataclasses import dataclass, field
from typing import List

from models.column_schema import ColumnSchema
from models.condition import Condition
from models.dimension import Dimension
from models.ranking import Ranking


@dataclass
class QueryPlan:
    """
    Represents a structured analytical query.
    """

    operation: str

    target_column: ColumnSchema

    dimensions: List[Dimension] = field(default_factory=list)

    conditions: List[Condition] = field(default_factory=list)

    ranking: Ranking | None = None
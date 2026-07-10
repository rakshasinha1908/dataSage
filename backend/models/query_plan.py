from dataclasses import dataclass, field
from typing import List

from models.column_schema import ColumnSchema


@dataclass
class QueryPlan:
    """
    Represents a structured analytical query.
    """

    operation: str

    target_column: ColumnSchema

    filters: List = field(default_factory=list)
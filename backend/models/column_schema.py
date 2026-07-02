from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class ColumnSchema:
    """
    Stores metadata about a single dataframe column.
    """

    name: str

    dtype: str

    nullable: bool

    unique_count: int

    sample_values: List[Any] = field(default_factory=list)
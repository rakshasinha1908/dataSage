from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class ColumnSchema:
    """
    Stores metadata about a single dataframe column.
    """

    name: str
    normalized_name: str
    dtype: str
    nullable: bool
    unique_count: int
    sample_values: List[Any] = field(default_factory=list)

    @property
    def is_numeric(self) -> bool:
        return self.dtype.startswith(("int", "float", "Int", "Float"))

    @property
    def is_boolean(self) -> bool:
        return self.dtype == "bool"

    @property
    def is_datetime(self) -> bool:
        return "datetime" in self.dtype
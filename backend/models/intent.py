from dataclasses import dataclass, field
from typing import Optional

from models.filter import Filter


@dataclass
class Intent:
    """
    Represents a fully structured user query.
    """

    operation: str

    target_column: str

    filters: list[Filter] = field(default_factory=list)

    group_by: Optional[str] = None

    sort_order: Optional[str] = None

    limit: Optional[int] = None
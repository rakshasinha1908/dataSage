from dataclasses import dataclass
from typing import Optional

from models.column_schema import ColumnSchema


@dataclass
class ValidationResult:
    """
    Represents the result of validating a parsed query.
    """

    success: bool

    column: Optional[ColumnSchema] = None

    error: Optional[str] = None
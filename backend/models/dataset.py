from dataclasses import dataclass, field
from typing import List, Optional

from models.column_schema import ColumnSchema
import pandas as pd


@dataclass
class Dataset:
    """
    Represents one uploaded dataset and all information associated with it.
    """

    dataframe: pd.DataFrame

    filename: str

    session_id: Optional[str] = None

    schema: List[ColumnSchema] = field(default_factory=list)
from dataclasses import dataclass, field
from typing import Dict

import pandas as pd


@dataclass
class Dataset:
    """
    Represents one uploaded dataset and all information associated with it.
    """

    dataframe: pd.DataFrame

    filename: str

    schema: Dict = field(default_factory=dict)
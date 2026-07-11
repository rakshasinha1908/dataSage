from dataclasses import dataclass


@dataclass
class Dimension:
    """
    Represents a grouping dimension in an analytical query.
    """

    column: str
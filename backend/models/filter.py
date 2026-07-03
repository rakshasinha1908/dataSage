from dataclasses import dataclass


@dataclass
class Filter:
    """
    Represents a single filtering condition.
    """

    column: str

    operator: str

    value: object
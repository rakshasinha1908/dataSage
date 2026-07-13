from dataclasses import dataclass


@dataclass
class Ranking:
    """
    Represents ranking instructions for grouped analytics.
    """

    direction: str  # "asc" or "desc"

    limit: int | None = None
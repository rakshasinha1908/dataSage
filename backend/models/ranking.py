from dataclasses import dataclass


@dataclass
class Ranking:
    """
    Represents ranking instructions extracted from a query.

    Ranking is used for operations where the user explicitly
    requests a subset of rows (e.g. "top 10 rows"),
    requests all rows (e.g. "show all rows"),
    or leaves the quantity unspecified, allowing the
    AnalyticsEngine to return a default preview.
    """

    direction: str | None = None

    limit: int | None = None

    is_explicit: bool = False

    show_all: bool = False
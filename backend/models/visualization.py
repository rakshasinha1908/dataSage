from dataclasses import dataclass


@dataclass
class Visualization:
    """
    Describes the recommended visualization
    for an analytical result.
    """

    chart_type: str

    x_axis: str | None = None

    y_axis: str | None = None

    title: str | None = None
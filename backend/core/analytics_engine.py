from models.dataset import Dataset
from models.column_schema import ColumnSchema


class AnalyticsEngine:
    """
    Executes deterministic analytical operations.
    """

    @staticmethod
    def _to_python(value):
        """
        Converts NumPy scalar values to native Python types.
        """

        if hasattr(value, "item"):
            return value.item()

        return value

    @classmethod
    def execute(
        cls,
        dataset: Dataset,
        operation: str,
        column: ColumnSchema,
    ):

        df = dataset.dataframe

        series = df[column.name]

        if operation == "mean":
            return cls._to_python(series.mean())

        if operation == "sum":
            return cls._to_python(series.sum())

        if operation == "count":
            return cls._to_python(series.count())

        if operation == "min":
            return cls._to_python(series.min())

        if operation == "max":
            return cls._to_python(series.max())

        raise ValueError(f"Unsupported operation: {operation}")
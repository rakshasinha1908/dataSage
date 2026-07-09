from models.dataset import Dataset
from models.column_schema import ColumnSchema
from models.operation import Operation


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

        if operation == Operation.MEAN:
            return cls._to_python(series.mean())

        if operation == Operation.SUM:
            return cls._to_python(series.sum())

        if operation == Operation.COUNT:
            return cls._to_python(series.count())

        if operation == Operation.MIN:
            return cls._to_python(series.min())

        if operation == Operation.MAX:
            return cls._to_python(series.max())

        raise ValueError(f"Unsupported operation: {operation}")
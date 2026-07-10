from models.dataset import Dataset
from models.column_schema import ColumnSchema
from models.operation import Operation
from models.query_plan import QueryPlan


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
        plan: QueryPlan,
    ):

        df = dataset.dataframe
        for condition in plan.conditions:
            if condition.operator == "==":
                df = df[
                    df[condition.column] == condition.value
                ]
        series = df[plan.target_column.name]

        if plan.operation == Operation.MEAN:
            return cls._to_python(series.mean())

        if plan.operation == Operation.SUM:
            return cls._to_python(series.sum())

        if plan.operation == Operation.COUNT:
            return cls._to_python(series.count())

        if plan.operation == Operation.MIN:
            return cls._to_python(series.min())

        if plan.operation == Operation.MAX:
            return cls._to_python(series.max())

        raise ValueError(f"Unsupported operation: {plan.operation}")
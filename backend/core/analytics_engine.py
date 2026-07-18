from models.dataset import Dataset
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
    def execute(cls, dataset: Dataset, plan: QueryPlan):
        df = dataset.dataframe

        # -------------------------------
        # Apply conditions
        # -------------------------------
        for condition in plan.conditions:
            if condition.operator == "==":
                df = df[df[condition.column] == condition.value]

        # -------------------------------
        # Dataset Preview
        # -------------------------------
        if plan.operation == Operation.HEAD:
            limit = (
                plan.ranking.limit
                if plan.ranking and plan.ranking.limit
                else 5
            )
            return df.head(limit).to_dict(orient="records")

        if plan.operation == Operation.TAIL:
            limit = (
                plan.ranking.limit
                if plan.ranking and plan.ranking.limit
                else 5
            )
            return df.tail(limit).to_dict(orient="records")

        # -------------------------------
        # Metadata
        # -------------------------------
        if plan.operation == "columns":
            return [
                {
                    "name": column.name,
                    "normalized_name": column.normalized_name,
                    "type": column.dtype,
                    "nullable": column.nullable,
                    "unique_values": column.unique_count,
                    "sample_values": column.sample_values,
                }
                for column in dataset.schema
            ]

        if plan.operation == "describe":
            return {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "numeric_columns": sum(
                    column.is_numeric for column in dataset.schema
                ),
                "categorical_columns": sum(
                    not column.is_numeric for column in dataset.schema
                ),
                "missing_values": int(df.isna().sum().sum()),
                "duplicate_rows": int(df.duplicated().sum()),
                "summary": df.describe(include="all").fillna("").to_dict(),
            }

        # -------------------------------
        # Dataset Analytics
        # -------------------------------
        if (
            plan.operation == Operation.COUNT
            and plan.target_column is None
        ):
            return cls._to_python(len(df))

        # -------------------------------
        # Grouped Analytics
        # -------------------------------
        if plan.dimensions:
            grouped = df.groupby(
                plan.dimensions[0].column
            )[plan.target_column.name]

            if plan.operation == Operation.MEAN:
                result = grouped.mean()
            elif plan.operation == Operation.SUM:
                result = grouped.sum()
            elif plan.operation == Operation.COUNT:
                result = grouped.count()
            elif plan.operation == Operation.MIN:
                result = grouped.min()
            elif plan.operation == Operation.MAX:
                result = grouped.max()
            else:
                raise ValueError(
                    f"Unsupported operation: {plan.operation}"
                )

            # -------------------------------
            # Ranking
            # -------------------------------
            if plan.ranking:
                ascending = plan.ranking.direction == "asc"
                result = result.sort_values(ascending=ascending)

                if plan.ranking.limit is not None:
                    result = result.head(plan.ranking.limit)

            return result.to_dict()

        # -------------------------------
        # Ungrouped Analytics
        # -------------------------------
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

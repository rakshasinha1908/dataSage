from models.dataset import Dataset
from models.operation import Operation
from models.query_plan import QueryPlan


class AnalyticsEngine:
    """
    Executes deterministic analytical operations.
    """

    DEFAULT_PREVIEW_ROWS = 25

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
                if plan.ranking is not None
                and plan.ranking.limit is not None
                else 5
            )

            return df.head(limit).to_dict(orient="records")

        if plan.operation == Operation.TAIL:
            limit = (
                plan.ranking.limit
                if plan.ranking is not None
                and plan.ranking.limit is not None
                else 5
            )

            return df.tail(limit).to_dict(orient="records")

        # -------------------------------
        # Row Retrieval
        # -------------------------------
        if plan.operation == Operation.SHOW_ROWS:

            total_matching_rows = len(df)

            if (
                plan.ranking is not None
                and plan.ranking.show_all
            ):
                preview_limit = total_matching_rows

            elif (
                plan.ranking is not None
                and plan.ranking.is_explicit
            ):
                preview_limit = min(
                    plan.ranking.limit,
                    total_matching_rows,
                )

            else:
                preview_limit = min(
                    cls.DEFAULT_PREVIEW_ROWS,
                    total_matching_rows,
                )

            preview = df.head(preview_limit)

            return {
                "rows": preview.to_dict(orient="records"),
                "returned_rows": len(preview),
                "total_matching_rows": total_matching_rows,
                "truncated": preview_limit < total_matching_rows,
            }

        # -------------------------------
        # Metadata
        # -------------------------------
        if plan.operation == Operation.COLUMNS:
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

        if plan.operation == Operation.DESCRIBE:
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

            # If the user explicitly asked for ascending/descending,
            # respect it. Otherwise, default to descending.
            if (
                plan.ranking is not None
                and plan.ranking.direction is not None
            ):
                ascending = plan.ranking.direction == "asc"
            else:
                ascending = False

            result = result.sort_values(
                ascending=ascending
            )

            # Apply Top-N / Bottom-N only if explicitly requested.
            if (
                plan.ranking is not None
                and plan.ranking.is_explicit
                and plan.ranking.limit is not None
            ):
                result = result.head(
                    plan.ranking.limit
                )

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

        raise ValueError(
            f"Unsupported operation: {plan.operation}"
        )
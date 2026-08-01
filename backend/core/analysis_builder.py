from models.query_plan import QueryPlan


class AnalysisBuilder:
    """
    Converts a QueryPlan into a
    human-readable analysis description.
    """

    OPERATION_NAMES = {
        "mean": "Average",
        "sum": "Total",
        "count": "Count",
        "min": "Minimum",
        "max": "Maximum",
    }

    @classmethod
    def build(
        cls,
        plan: QueryPlan,
    ) -> str:

        lines = []

        operation = cls.OPERATION_NAMES.get(
            plan.operation,
            str(plan.operation).title(),
        )

        # -----------------------------------
        # Analytical operation
        # -----------------------------------

        if plan.target_column is not None:

            lines.append(
                f"{operation} "
                f"{plan.target_column.normalized_name.title()}"
            )

        elif plan.operation == "count":

            # COUNT can operate on rows without
            # requiring a target column.
            lines.append("Count of rows")

        else:

            lines.append(operation)

        # -----------------------------------
        # Grouping dimensions
        # -----------------------------------

        if plan.dimensions:

            dimension_names = [
                dimension.column
                .replace("_", " ")
                .title()
                for dimension in plan.dimensions
            ]

            lines.append(
                f"Grouped by {', '.join(dimension_names)}"
            )

        # -----------------------------------
        # Filters
        # -----------------------------------

        if plan.conditions:

            for condition in plan.conditions:

                column_name = (
                    condition.column
                    .replace("_", " ")
                    .title()
                )

                lines.append(
                    f"Filtered where "
                    f"{column_name} "
                    f"{condition.operator} "
                    f"{condition.value}"
                )

        # -----------------------------------
        # Ranking
        # -----------------------------------

        if plan.ranking:

            direction = (
                "Top"
                if plan.ranking.direction == "desc"
                else "Bottom"
            )

            if plan.ranking.limit is not None:
                lines.append(
                    f"{direction} {plan.ranking.limit}"
                )

        return "\n".join(lines)
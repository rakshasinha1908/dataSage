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
            plan.operation.title(),
        )

        lines.append(
            f"{operation} {plan.target_column.normalized_name.title()}"
        )

        if plan.dimensions:
            lines.append(
                f"Grouped by {plan.dimensions[0].column.replace('_', ' ').title()}"
            )

        if plan.conditions:
            for condition in plan.conditions:
                lines.append(
                    f"Filtered where {condition.column.replace('_', ' ').title()} = {condition.value}"
                )

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
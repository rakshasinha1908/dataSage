from models.query_plan import QueryPlan
from models.visualization import Visualization
from models.operation import Operation


class VisualizationSelector:
    """
    Chooses the best visualization
    for a query result.
    """

    # Operations that should never produce charts.
    NO_VISUALIZATION_OPERATIONS = {
        Operation.HEAD,
        Operation.TAIL,
        "describe",
        "columns",
        "schema",
        "summary",
    }

    @classmethod
    def select(
        cls,
        plan: QueryPlan,
        result,
    ):

        # -----------------------------------
        # Dataset metadata / previews
        # -----------------------------------
        if plan.operation in cls.NO_VISUALIZATION_OPERATIONS:
            return None

        # -----------------------------------
        # Scalar values don't need charts.
        #
        # Grouped analytical results are
        # represented as dictionaries.
        # -----------------------------------
        if not isinstance(result, dict):
            return None

        # -----------------------------------
        # A grouped visualization requires
        # at least one dimension.
        # -----------------------------------
        if not plan.dimensions:
            return None

        # -----------------------------------
        # Most grouped aggregations require
        # a target column.
        #
        # COUNT is the exception because it
        # counts rows within each group.
        # -----------------------------------
        if (
            plan.operation != Operation.COUNT
            and plan.target_column is None
        ):
            return None

        operation_names = {
            Operation.MEAN: "Average",
            Operation.SUM: "Total",
            Operation.COUNT: "Count",
            Operation.MIN: "Minimum",
            Operation.MAX: "Maximum",
        }

        operation_name = operation_names.get(
            plan.operation,
            str(plan.operation).title(),
        )

        dimension_name = (
            plan.dimensions[0]
            .column
            .replace("_", " ")
            .title()
        )

        # -----------------------------------
        # Grouped COUNT
        #
        # ResponseBuilder normalizes grouped
        # results into:
        #
        # {
        #     "label": group,
        #     "value": count,
        # }
        # -----------------------------------
        if plan.operation == Operation.COUNT:
            return Visualization(
                chart_type="bar",
                x_axis="label",
                y_axis="value",
                title=f"Count by {dimension_name}",
            )

        # -----------------------------------
        # Grouped analytical measure
        # -----------------------------------
        return Visualization(
            chart_type="bar",
            x_axis="label",
            y_axis="value",
            title=(
                f"{operation_name} "
                f"{plan.target_column.normalized_name.title()} "
                f"by {dimension_name}"
            ),
        )
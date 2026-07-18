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
    def select(cls, plan: QueryPlan, result):

        # -----------------------------------
        # Dataset metadata / previews
        # -----------------------------------
        if plan.operation in cls.NO_VISUALIZATION_OPERATIONS:
            return None

        # -----------------------------------
        # Scalar values don't need charts.
        # Example:
        # average salary
        # maximum height
        # count rows
        # -----------------------------------
        if not isinstance(result, dict):
            return None

        # -----------------------------------
        # Grouped results require both
        # a dimension and a target column.
        # -----------------------------------
        if (
            not plan.dimensions
            or plan.target_column is None
        ):
            return None

        operation_names = {
            "mean": "Average",
            "sum": "Total",
            "count": "Count",
            "min": "Minimum",
            "max": "Maximum",
        }

        operation_name = operation_names.get(
            plan.operation,
            str(plan.operation).title(),
        )

        return Visualization(
            chart_type="bar",
            x_axis=plan.dimensions[0].column,
            y_axis=plan.target_column.name,
            title=(
                f"{operation_name} "
                f"{plan.target_column.normalized_name.title()} "
                f"by "
                f"{plan.dimensions[0].column.replace('_', ' ').title()}"
            ),
        )
from models.query_plan import QueryPlan
from models.visualization import Visualization


class VisualizationSelector:
    """
    Chooses the best visualization
    for a query result.
    """

    @classmethod
    def select(cls, plan: QueryPlan, result):
        # Scalar result → no visualization
        if not isinstance(result, dict):
            return None

        # Define operation name mappings
        operation_names = {
            "mean": "Average",
            "sum": "Total",
            "count": "Count",
            "min": "Minimum",
            "max": "Maximum",
        }

        operation_name = operation_names.get(
            plan.operation,
            plan.operation.title(),
        )

        # Grouped result → Bar Chart
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

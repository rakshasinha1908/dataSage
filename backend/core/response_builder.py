from numbers import Number


class ResponseBuilder:
    """
    Converts analytical results into frontend-ready response objects.
    """

    @staticmethod
    def build(plan, result, visualization):

        if isinstance(result, Number):
            return ResponseBuilder._build_kpi(plan, result)

        if isinstance(result, list):
            return ResponseBuilder._build_table(plan, result)

        if isinstance(result, dict):
            return ResponseBuilder._build_grouped(
                plan,
                result,
                visualization,
            )

        raise ValueError(
            f"Unsupported response type: {type(result)}"
        )

    @staticmethod
    def _build_kpi(plan, result):
        """
        Builds a KPI response for scalar analytical results.
        """
        return {
            "type": "kpi",
            "title": ResponseBuilder._generate_title(plan),
            "value": result,
            "insight": None,
        }

    @staticmethod
    def _build_table(plan, result):
        """
        Builds a structured table response.
        """
        return {
            "type": "structured",
            "title": ResponseBuilder._generate_title(plan),
            "table": result,
            "chart": None,
            "insight": None,
        }

    @staticmethod
    def _build_grouped(plan, result, visualization):
        """
        Builds a grouped analytical response.
        """
        table = [
            {"label": key, "value": value}
            for key, value in result.items()
        ]

        return {
            "type": "structured",
            "title": ResponseBuilder._generate_title(plan),
            "table": table,
            "chart": visualization,
            "insight": None,
        }

    @staticmethod
    def _generate_title(plan):
        """
        Generates a human-readable title from the query plan.
        """
        operation_titles = {
            "mean": "Average",
            "sum": "Total",
            "count": "Count",
            "min": "Minimum",
            "max": "Maximum",
            "head": "Top Rows",
            "tail": "Bottom Rows",
        }

        title = operation_titles.get(plan.operation, "Result")

        if plan.target_column is not None:
            title += f" {plan.target_column.name.replace('_', ' ').title()}"

        if plan.dimensions:
            dimension = plan.dimensions[0].column
            title += f" by {dimension.replace('_', ' ').title()}"

        return title

from numbers import Number

from models.operation import Operation


class ResponseBuilder:
    """
    Converts analytical results into frontend-ready response objects.
    """

    @staticmethod
    def build(plan, result, visualization):

        # -----------------------------------
        # SHOW_ROWS
        # -----------------------------------
        if plan.operation == Operation.SHOW_ROWS:
            return ResponseBuilder._build_row_preview(
                plan,
                result,
            )

        # -----------------------------------
        # KPI
        # -----------------------------------
        if isinstance(result, Number):
            return ResponseBuilder._build_kpi(
                plan,
                result,
            )

        # -----------------------------------
        # Metadata tables
        # -----------------------------------
        if isinstance(result, list):
            return ResponseBuilder._build_table(
                plan,
                result,
            )

        # -----------------------------------
        # Grouped analytics
        # -----------------------------------
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
            "success": True,
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
            "success": True,
            "type": "structured",
            "title": ResponseBuilder._generate_title(plan),
            "table": result,
            "metadata": None,
            "chart": None,
            "insight": None,
        }

    @staticmethod
    def _build_row_preview(plan, result):
        """
        Builds a structured response for row previews.
        """

        return {
            "success": True,
            "type": "structured",
            "title": "Rows",
            "table": result["rows"],
            "metadata": {
                "returned_rows": result["returned_rows"],
                "total_matching_rows": result[
                    "total_matching_rows"
                ],
                "truncated": result["truncated"],
            },
            "chart": None,
            "insight": None,
        }

    @staticmethod
    def _build_grouped(
        plan,
        result,
        visualization,
    ):
        """
        Builds a grouped analytical response.
        """

        table = [
            {
                "label": key,
                "value": value,
            }
            for key, value in result.items()
        ]

        return {
            "success": True,
            "type": "structured",
            "title": ResponseBuilder._generate_title(
                plan
            ),
            "table": table,
            "metadata": None,
            "chart": visualization,
            "insight": None,
        }

    @staticmethod
    def _generate_title(plan):
        """
        Generates a human-readable title from the query plan.
        """

        operation_titles = {
            Operation.MEAN: "Average",
            Operation.SUM: "Total",
            Operation.COUNT: "Count",
            Operation.MIN: "Minimum",
            Operation.MAX: "Maximum",
            Operation.HEAD: "Top Rows",
            Operation.TAIL: "Bottom Rows",
            Operation.SHOW_ROWS: "Rows",
            Operation.COLUMNS: "Columns",
            Operation.DESCRIBE: "Dataset Summary",
        }

        title = operation_titles.get(
            plan.operation,
            "Result",
        )

        if plan.target_column is not None:
            title += (
                f" {plan.target_column.name.replace('_', ' ').title()}"
            )

        if plan.dimensions:
            dimension = plan.dimensions[0].column
            title += (
                f" by {dimension.replace('_', ' ').title()}"
            )

        return title
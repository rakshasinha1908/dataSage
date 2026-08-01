from numbers import Number

from models.operation import Operation


class ResponseBuilder:
    """
    Converts analytical results into frontend-ready response objects.
    """

    @staticmethod
    def build(plan, result, visualization):

        # -----------------------------------
        # Analytical failure
        # -----------------------------------
        if (
            isinstance(result, dict)
            and result.get("success") is False
        ):
            return result

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

        Titles reflect:
        - analytical operation
        - target measure
        - grouping dimension
        - ranking direction / limit when applicable
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

        operation_title = operation_titles.get(
            plan.operation,
            "Result",
        )

        # -----------------------------------
        # Human-readable target column
        # -----------------------------------

        target_title = ""

        if plan.target_column is not None:
            target_title = (
                plan.target_column.name
                .replace("_", " ")
                .title()
            )

        # -----------------------------------
        # Human-readable dimension
        # -----------------------------------

        dimension_title = ""

        if plan.dimensions:
            dimension_title = (
                plan.dimensions[0]
                .column
                .replace("_", " ")
                .title()
            )

        # -----------------------------------
        # Ranking-aware grouped titles
        # -----------------------------------

        if (
            plan.ranking is not None
            and dimension_title
        ):
            ranking = plan.ranking

            # --------------------------------
            # Explicit ranking:
            #
            # top 3 cartoons by average...
            # bottom 5 cities by total...
            # --------------------------------

            if (
                ranking.is_explicit
                and ranking.limit is not None
                and ranking.direction is not None
            ):
                ranking_word = (
                    "Top"
                    if ranking.direction == "desc"
                    else "Bottom"
                )

                title = (
                    f"{ranking_word} "
                    f"{ranking.limit} "
                    f"{dimension_title}"
                )

                if target_title:
                    title += (
                        f" by "
                        f"{operation_title} "
                        f"{target_title}"
                    )

                return title

            # --------------------------------
            # Implicit singular ranking:
            #
            # highest average...
            # lowest average...
            #
            # RankingParser uses limit=1 for
            # these queries.
            # --------------------------------

            if (
                not ranking.is_explicit
                and ranking.limit == 1
                and ranking.direction is not None
            ):
                ranking_word = (
                    "Highest"
                    if ranking.direction == "desc"
                    else "Lowest"
                )

                title = (
                    f"{ranking_word} "
                    f"{operation_title}"
                )

                if target_title:
                    title += f" {target_title}"

                title += f" by {dimension_title}"

                return title

        # -----------------------------------
        # Standard non-ranking title
        # -----------------------------------

        title = operation_title

        if target_title:
            title += f" {target_title}"

        if dimension_title:
            title += f" by {dimension_title}"

        return title

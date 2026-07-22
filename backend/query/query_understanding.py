from models.column_schema import ColumnSchema
from models.query_plan import QueryPlan

from query.query_normalizer import QueryNormalizer
from query.operation_parser import OperationParser
from query.condition_parser import ConditionParser
from query.ranking_parser import RankingParser
from query.dimension_parser import DimensionParser
from query.column_matcher import ColumnMatcher
from query.ranking_analytics_parser import RankingAnalyticsParser

from models.dimension import Dimension
from models.operation import Operation


class QueryUnderstanding:
    """
    Responsible for converting a natural language question into a QueryPlan.

    Responsibilities
    ----------------
    - Normalize the question
    - Extract the requested operation
    - Extract filtering conditions
    - Extract ranking information
    - Extract grouping dimensions
    - Match user references to dataset columns
    - Construct and return a QueryPlan
    """

    @classmethod
    def parse(
        cls,
        question: str,
        schema: list[ColumnSchema],
    ) -> QueryPlan:

        # ----------------------------------------
        # Normalize query
        # ----------------------------------------

        normalized_question = QueryNormalizer.normalize(question)

        parsed = OperationParser.parse(normalized_question)

        operation = parsed["operation"]

        # ----------------------------------------
        # Extract conditions
        # ----------------------------------------

        condition_result = ConditionParser.parse(
            parsed["remaining_text"],
            schema,
        )

        # ----------------------------------------
        # Dataset preview operations
        # ----------------------------------------

        if operation in (
            Operation.SHOW_ROWS,
            Operation.HEAD,
            Operation.TAIL,
        ):

            ranking_result = RankingParser.parse(
                condition_result.cleaned_text,
            )
            print("====================================")
            print("Preview Operation :", operation)
            print("Ranking :", ranking_result.ranking)
            print("====================================")

            return QueryPlan(
                operation=operation,
                target_column=None,
                dimensions=[],
                conditions=condition_result.conditions,
                ranking=ranking_result.ranking,
            )

        # ----------------------------------------
        # Analytical operations
        # ----------------------------------------

        ranking_result = RankingParser.parse(
            condition_result.cleaned_text,
        )

        dimensions = []
        measure_columns = []

        if ranking_result.ranking is not None:

            analytics_result = RankingAnalyticsParser.parse(
                ranking_result.cleaned_text,
            )

            if analytics_result.group_phrase:

                group_columns = ColumnMatcher.match(
                    analytics_result.group_phrase,
                    schema,
                )

                if group_columns:

                    dimensions.append(
                        Dimension(
                            column=group_columns[0].name
                        )
                    )

            if analytics_result.measure_phrase:

                measure_columns = ColumnMatcher.match(
                    analytics_result.measure_phrase,
                    schema,
                )

            if (
                operation is None
                and measure_columns
                and measure_columns[0].is_numeric
            ):
                operation = Operation.SUM

        else:

            dimension_result = DimensionParser.parse(
                ranking_result.cleaned_text,
                schema,
            )

            measure_columns = ColumnMatcher.match(
                dimension_result.cleaned_text,
                schema,
            )

            dimensions = dimension_result.dimensions
            
        print("====================================")
        print("Operation :", operation)
        print("Ranking   :", ranking_result.ranking)
        print("====================================")

        return QueryPlan(
            operation=operation or Operation.SUM,
            target_column=measure_columns[0] if measure_columns else None,
            dimensions=dimensions,
            conditions=condition_result.conditions,
            ranking=ranking_result.ranking,
        )
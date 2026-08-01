from models.column_schema import ColumnSchema
from models.query_plan import QueryPlan

from query.query_normalizer import QueryNormalizer
from query.operation_parser import OperationParser
from query.condition_parser import ConditionParser
from query.ranking_parser import RankingParser
from query.dimension_parser import DimensionParser
from query.column_matcher import ColumnMatcher
from query.ranking_analytics_parser import RankingAnalyticsParser
from query.measure_resolver import MeasureResolver
from query.measure_candidate_parser import MeasureCandidateParser
from query.filter_value_resolver import FilterValueResolver
from query.numeric_filter_parser import NumericFilterParser

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

    @staticmethod
    def _print_debug_summary(
        question: str,
        normalized_question: str,
        operation,
        target_column,
        dimensions,
        conditions,
        ranking,
    ):
        """
        Prints one compact summary of the final query understanding.

        Individual parsers should remain mostly silent so terminal
        output stays readable during debugging.
        """

        print("\n" + "=" * 60)
        print("QUERY UNDERSTANDING")
        print("=" * 60)

        print("Question      :", question)
        print("Normalized    :", normalized_question)
        print("Operation     :", operation)

        print(
            "Target Column :",
            target_column.name
            if target_column is not None
            else None,
        )

        print(
            "Dimensions    :",
            [
                dimension.column
                for dimension in dimensions
            ],
        )

        print("Conditions    :", conditions)
        print("Ranking       :", ranking)

        print("=" * 60)

    @classmethod
    def parse(
        cls,
        question: str,
        schema: list[ColumnSchema],
    ) -> QueryPlan:

        # ----------------------------------------
        # Normalize query
        # ----------------------------------------
        normalized_question = QueryNormalizer.normalize(
            question
        )

        parsed = OperationParser.parse(
            normalized_question
        )

        operation = parsed["operation"]

        # ----------------------------------------
        # Extract categorical / boolean conditions
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

            cls._print_debug_summary(
                question=question,
                normalized_question=normalized_question,
                operation=operation,
                target_column=None,
                dimensions=[],
                conditions=condition_result.conditions,
                ranking=ranking_result.ranking,
            )

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

        dimensions: list[Dimension] = []
        measure_columns: list[ColumnSchema] = []

        # ----------------------------------------
        # Ranking analytics
        # ----------------------------------------
        if ranking_result.ranking is not None:

            analytics_result = RankingAnalyticsParser.parse(
                ranking_result.cleaned_text,
            )

            # ------------------------------------
            # Resolve grouping dimension
            # ------------------------------------
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

            # ------------------------------------
            # Resolve ranking measure
            # ------------------------------------
            if analytics_result.measure_phrase:

                candidate_result = (
                    MeasureCandidateParser.parse(
                        analytics_result.measure_phrase,
                    )
                )

                resolved_measure, remaining_text = (
                    MeasureResolver.resolve(
                        candidate_result,
                        schema,
                    )
                )

                measure_columns = (
                    [resolved_measure]
                    if resolved_measure is not None
                    else []
                )

            # ------------------------------------
            # Infer SUM for numeric ranking measure
            # ------------------------------------
            if (
                operation is None
                and measure_columns
                and measure_columns[0].is_numeric
            ):
                operation = Operation.SUM

        # ----------------------------------------
        # Non-ranking analytics
        # ----------------------------------------
        else:

            # ------------------------------------
            # Resolve analytical measure
            # ------------------------------------
            candidate_result = MeasureCandidateParser.parse(
                ranking_result.cleaned_text,
            )

            resolved_measure, remaining_text = (
                MeasureResolver.resolve(
                    candidate_result,
                    schema,
                )
            )

            measure_columns = (
                [resolved_measure]
                if resolved_measure is not None
                else []
            )

            # ------------------------------------
            # Resolve dimensions
            # ------------------------------------
            dimension_result = DimensionParser.parse(
                remaining_text,
                schema,
            )

            dimensions = dimension_result.dimensions

            # ------------------------------------
            # Resolve categorical / value filters
            # ------------------------------------
            resolved_conditions, remaining_text = (
                FilterValueResolver.resolve(
                    dimension_result.cleaned_text,
                    schema,
                )
            )

            condition_result.conditions.extend(
                resolved_conditions
            )

            # ------------------------------------
            # Resolve numeric filters
            # ------------------------------------
            numeric_result = NumericFilterParser.parse(
                remaining_text,
                schema,
            )

            condition_result.conditions.extend(
                numeric_result.conditions
            )

            remaining_text = numeric_result.cleaned_text

        # ----------------------------------------
        # Finalize query plan
        # ----------------------------------------
        final_operation = operation or Operation.SUM

        target_column = (
            measure_columns[0]
            if measure_columns
            else None
        )

        # ----------------------------------------
        # Compact debug summary
        # ----------------------------------------
        cls._print_debug_summary(
            question=question,
            normalized_question=normalized_question,
            operation=final_operation,
            target_column=target_column,
            dimensions=dimensions,
            conditions=condition_result.conditions,
            ranking=ranking_result.ranking,
        )

        return QueryPlan(
            operation=final_operation,
            target_column=target_column,
            dimensions=dimensions,
            conditions=condition_result.conditions,
            ranking=ranking_result.ranking,
        )
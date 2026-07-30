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

            print("\n===== RANKING DEBUG =====")
            print("Input:", condition_result.cleaned_text)
            print("Ranking:", ranking_result.ranking)
            print("Cleaned:", ranking_result.cleaned_text)
            print("=========================\n")

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

        print("\n" + "=" * 60)
        print("🔥 QUERY UNDERSTANDING")
        print("Condition Text :", repr(condition_result.cleaned_text))
        print("Cleaned Text   :", repr(ranking_result.cleaned_text))
        print("Ranking        :", ranking_result.ranking)
        print("=" * 60)

        dimensions: list[Dimension] = []
        measure_columns: list[ColumnSchema] = []

        if ranking_result.ranking is not None:
            analytics_result = RankingAnalyticsParser.parse(
                ranking_result.cleaned_text,
            )

            print("\n" + "=" * 60)
            print("🔥 RANKING ANALYTICS")
            print("Input          :", repr(ranking_result.cleaned_text))
            print("Group Phrase   :", repr(analytics_result.group_phrase))
            print("Measure Phrase :", repr(analytics_result.measure_phrase))
            print("Cleaned Text   :", repr(analytics_result.cleaned_text))
            print("=" * 60)

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
                candidate_result = MeasureCandidateParser.parse(
                    analytics_result.measure_phrase,
                )

                resolved_measure, remaining_text = MeasureResolver.resolve(
                    candidate_result,
                    schema,
                )

                measure_columns = (
                    [resolved_measure]
                    if resolved_measure
                    else []
                )

            if (
                operation is None
                and measure_columns
                and measure_columns[0].is_numeric
            ):
                operation = Operation.SUM

        else:
            candidate_result = MeasureCandidateParser.parse(
                ranking_result.cleaned_text,
            )

            resolved_measure, remaining_text = MeasureResolver.resolve(
                candidate_result,
                schema,
            )

            measure_columns = (
                [resolved_measure]
                if resolved_measure is not None
                else []
            )

            dimension_result = DimensionParser.parse(
                remaining_text,
                schema,
            )

            dimensions = dimension_result.dimensions

            resolved_conditions, remaining_text = FilterValueResolver.resolve(
                dimension_result.cleaned_text,
                schema,
            )

            condition_result.conditions.extend(resolved_conditions)
            
            print("\n" + "=" * 60)
            print("🔥 FILTER VALUE RESOLVER")
            print("Conditions    :", resolved_conditions)
            print("Remaining Text:", repr(remaining_text))
            print("=" * 60)

            print("\n" + "=" * 60)
            print("🔥 DIMENSION PARSER")
            print("Dimensions    :", dimension_result.dimensions)
            print("Remaining Text:", repr(dimension_result.cleaned_text))
            print("=" * 60)

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

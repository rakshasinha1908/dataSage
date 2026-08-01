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
from query.comparison_dimension_parser import (
    ComparisonDimensionParser,
)

from utils.text_utils import remove_filler_words

from models.dimension import Dimension
from models.operation import Operation


class QueryUnderstanding:
    """
    Responsible for converting a natural language question
    into a QueryPlan.
    """

    COUNT_ENTITY_WORDS = {
        "customer",
        "customers",
        "patient",
        "patients",
        "record",
        "records",
        "row",
        "rows",
        "entry",
        "entries",
    }

    @staticmethod
    def _print_debug_summary(
        question: str,
        normalized_question: str,
        operation,
        target_column,
        dimensions,
        conditions,
        ranking,
        unresolved_text: str = "",
    ):
        print("\n" + "=" * 60)
        print("QUERY UNDERSTANDING")
        print("=" * 60)

        print("Question      :", question)
        print("Normalized    :", normalized_question)
        print("Operation     :", operation)

        print(
            "Target Column :",
            target_column.name if target_column is not None else None,
        )

        print(
            "Dimensions    :",
            [dimension.column for dimension in dimensions],
        )

        print("Conditions    :", conditions)
        print("Ranking       :", ranking)
        print("Unresolved    :", repr(unresolved_text))

        print("=" * 60)

    # =========================================================
    # COUNT helpers
    # =========================================================

    @classmethod
    def _remove_count_entity_words(cls, text: str) -> str:
        words = text.split()
        cleaned_words = [
            word for word in words if word not in cls.COUNT_ENTITY_WORDS
        ]
        return " ".join(cleaned_words)

    @classmethod
    def _prepare_measure_text(cls, operation, text: str) -> str:
        cleaned_text = remove_filler_words(text)
        if operation == Operation.COUNT:
            cleaned_text = cls._remove_count_entity_words(cleaned_text)
        return " ".join(cleaned_text.split())

    # =========================================================
    # Main parser
    # =========================================================

    @classmethod
    def parse(cls, question: str, schema: list[ColumnSchema]) -> QueryPlan:
        normalized_question = QueryNormalizer.normalize(question)

        parsed = OperationParser.parse(normalized_question)
        operation = parsed["operation"]

        condition_result = ConditionParser.parse(
            parsed["remaining_text"], schema
        )

        if operation in (
            Operation.SHOW_ROWS,
            Operation.HEAD,
            Operation.TAIL,
        ):
            ranking_result = RankingParser.parse(
                condition_result.cleaned_text,
            )

            unresolved_text = ranking_result.cleaned_text

            cls._print_debug_summary(
                question=question,
                normalized_question=normalized_question,
                operation=operation,
                target_column=None,
                dimensions=[],
                conditions=condition_result.conditions,
                ranking=ranking_result.ranking,
                unresolved_text=unresolved_text,
            )

            return QueryPlan(
                operation=operation,
                target_column=None,
                dimensions=[],
                conditions=condition_result.conditions,
                ranking=ranking_result.ranking,
                unresolved_text=unresolved_text,
            )

        ranking_result = RankingParser.parse(
            condition_result.cleaned_text,
        )

        dimensions: list[Dimension] = []
        measure_columns: list[ColumnSchema] = []

        remaining_text = ranking_result.cleaned_text

        if ranking_result.ranking is not None:
            analytics_result = RankingAnalyticsParser.parse(
                ranking_result.cleaned_text,
            )

            if analytics_result.group_phrase:
                group_columns = ColumnMatcher.match(
                    analytics_result.group_phrase, schema
                )
                if group_columns:
                    dimensions.append(
                        Dimension(column=group_columns[0].name)
                    )

            if analytics_result.measure_phrase:
                measure_phrase = analytics_result.measure_phrase
                if operation == Operation.COUNT:
                    measure_phrase = cls._remove_count_entity_words(
                        measure_phrase
                    )

                candidate_result = MeasureCandidateParser.parse(
                    measure_phrase,
                )

                resolved_measure, remaining_text = MeasureResolver.resolve(
                    candidate_result, schema
                )

                measure_columns = (
                    [resolved_measure] if resolved_measure is not None else []
                )

            remaining_text = ""

        else:
            measure_text = cls._prepare_measure_text(
                operation, ranking_result.cleaned_text
            )

            candidate_result = MeasureCandidateParser.parse(measure_text)

            resolved_measure, remaining_text = MeasureResolver.resolve(
                candidate_result, schema
            )

            measure_columns = (
                [resolved_measure] if resolved_measure is not None else []
            )

            # ------------------------------------
            # Resolve dimensions
            # ------------------------------------
            dimension_result = DimensionParser.parse(
                remaining_text,
                schema,
            )

            dimensions = dimension_result.dimensions
            remaining_text = dimension_result.cleaned_text

            # ------------------------------------
            # Resolve implicit comparison dimension
            # ------------------------------------
            if not dimensions:
                comparison_result = ComparisonDimensionParser.parse(
                    remaining_text,
                    schema,
                    original_text=normalized_question,
                )

                if comparison_result.dimensions:
                    dimensions = comparison_result.dimensions

                # IMPORTANT: Continue with the text left after comparison parsing.
                remaining_text = comparison_result.cleaned_text

            # ------------------------------------
            # Resolve categorical / value filters
            # ------------------------------------
            resolved_conditions, remaining_text = FilterValueResolver.resolve(
                remaining_text,
                schema,
            )

            condition_result.conditions.extend(resolved_conditions)

            # ------------------------------------
            # Resolve numeric filters
            # ------------------------------------
            numeric_result = NumericFilterParser.parse(
                remaining_text,
                schema,
            )

            condition_result.conditions.extend(numeric_result.conditions)
            remaining_text = numeric_result.cleaned_text

        final_operation = operation or Operation.SUM

        target_column = measure_columns[0] if measure_columns else None

        cls._print_debug_summary(
            question=question,
            normalized_question=normalized_question,
            operation=final_operation,
            target_column=target_column,
            dimensions=dimensions,
            conditions=condition_result.conditions,
            ranking=ranking_result.ranking,
            unresolved_text=remaining_text,
        )

        return QueryPlan(
            operation=final_operation,
            target_column=target_column,
            dimensions=dimensions,
            conditions=condition_result.conditions,
            ranking=ranking_result.ranking,
            unresolved_text=remaining_text,
        )

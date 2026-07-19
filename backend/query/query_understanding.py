from models.column_schema import ColumnSchema
from models.query_plan import QueryPlan

from query.query_normalizer import QueryNormalizer
from query.operation_parser import OperationParser
from query.condition_parser import ConditionParser
from query.ranking_parser import RankingParser
from query.dimension_parser import DimensionParser
from query.column_matcher import ColumnMatcher


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

    This class does NOT:
    - Execute analytics
    - Validate business logic
    - Generate responses
    - Know anything about FastAPI
    """

    @classmethod
    def parse(
        cls,
        question: str,
        schema: list[ColumnSchema],
    ) -> QueryPlan:

        normalized_question = QueryNormalizer.normalize(question)

        parsed = OperationParser.parse(normalized_question)

        condition_result = ConditionParser.parse(
            parsed["remaining_text"],
            schema,
        )

        ranking_result = RankingParser.parse(
            condition_result.cleaned_text,
        )

        dimension_result = DimensionParser.parse(
            ranking_result.cleaned_text,
            schema,
        )

        print("=" * 60)
        print("Remaining text after OperationParser :", parsed["remaining_text"])
        print("After ConditionParser               :", condition_result.cleaned_text)
        print("After RankingParser                 :", ranking_result.cleaned_text)
        print("After DimensionParser               :", dimension_result.cleaned_text)
        print("Dimensions                          :", [d.column for d in dimension_result.dimensions])
        print("=" * 60)

        print("\nCalling ColumnMatcher...\n")

        matched_columns = ColumnMatcher.match(
            dimension_result.cleaned_text,
            schema,
        )

        print("\nReturned from ColumnMatcher.\n")

        return QueryPlan(
            operation=parsed["operation"],
            target_column=matched_columns[0] if matched_columns else None,
            dimensions=dimension_result.dimensions,
            conditions=condition_result.conditions,
            ranking=ranking_result.ranking,
        )
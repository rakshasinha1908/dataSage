from fastapi import APIRouter, HTTPException

from storage.session_manager import SessionManager

import query.operation_parser as op
import query.dimension_parser as dp
import query.column_matcher as cm
import query.condition_parser as cp
import query.ranking_parser as rp
import query.intent_validator as iv

print("=" * 80)
print("USING MODULES")
print("OperationParser :", op.__file__)
print("ConditionParser :", cp.__file__)
print("RankingParser   :", rp.__file__)
print("DimensionParser :", dp.__file__)
print("ColumnMatcher   :", cm.__file__)
print("IntentValidator :", iv.__file__)
print("=" * 80)

OperationParser = op.OperationParser
ConditionParser = cp.ConditionParser
RankingParser = rp.RankingParser
DimensionParser = dp.DimensionParser
ColumnMatcher = cm.ColumnMatcher
IntentValidator = iv.IntentValidator

from core.analytics_engine import AnalyticsEngine
from core.visualization_selector import VisualizationSelector

from models.query_plan import QueryPlan
from models.response import Response
from core.response_builder import ResponseBuilder
from models.query_context import QueryContext
from query.query_normalizer import QueryNormalizer
from query.query_understanding import QueryUnderstanding


router = APIRouter(prefix="/query", tags=["Query"])


@router.get("/")
def query_dataset(session_id: str, question: str):

    dataset = SessionManager.get(session_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid session ID.",
        )

    print("\n================ DATASET SCHEMA ================")
    # =====================================================
    # TODO:
    # Move query parsing pipeline into QueryUnderstanding
    # =====================================================

    for column in dataset.schema:
        print(
            f"{column.name} ---> {column.normalized_name} | samples={column.sample_values}"
        )

    print("===============================================\n")

    normalized_question = QueryNormalizer.normalize(question)

    parsed = OperationParser.parse(normalized_question)

    condition_result = ConditionParser.parse(
        parsed["remaining_text"],
        dataset.schema,
    )

    ranking_result = RankingParser.parse(
        condition_result.cleaned_text,
    )

    dimension_result = DimensionParser.parse(
        ranking_result.cleaned_text,
        dataset.schema,
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
        dataset.schema,
    )

    print("\nReturned from ColumnMatcher.\n")

    validation = IntentValidator.validate(
        parsed["operation"],
        matched_columns,
    )

    print("=" * 60)
    print("Question          :", question)
    print("Operation         :", parsed["operation"])
    print("Matched Columns   :", [c.name for c in matched_columns])
    print("Validation        :", validation.success)
    print("Validation Error  :", validation.error)
    print("=" * 60)

    if not validation.success:
        return Response(
            success=False,
            answer=None,
            visualization=None,
            can_explain=False,
            error=validation.error,
        )

    # plan = QueryPlan(
    #     operation=parsed["operation"],
    #     target_column=validation.column,
    #     dimensions=dimension_result.dimensions,
    #     conditions=condition_result.conditions,
    #     ranking=ranking_result.ranking,
    # )
    plan = QueryUnderstanding.parse(
        question,
        dataset.schema,
    )

    result = AnalyticsEngine.execute(
        dataset,
        plan,
    )

    visualization = VisualizationSelector.select(
        plan,
        result,
    )

    response = ResponseBuilder.build(
        plan,
        result,
        visualization,
    )

    query_context = QueryContext(
        question=question,
        query_plan=plan,
        response=response,
    )

    SessionManager.save_query_context(
        session_id,
        query_context,
    )

    return response
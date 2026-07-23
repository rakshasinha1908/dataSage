from core.analytics_engine import AnalyticsEngine
from core.response_builder import ResponseBuilder
from core.visualization_selector import VisualizationSelector

from query.intent_validator import IntentValidator
from query.query_understanding import QueryUnderstanding


class QueryEngine:

    @staticmethod
    def execute(dataset, question):

        print("\n================ DATASET SCHEMA ================")

        for column in dataset.schema:
            print(
                f"{column.name} ---> {column.normalized_name} | samples={column.sample_values}"
            )

        print("===============================================\n")

        plan = QueryUnderstanding.parse(
            question,
            dataset.schema,
        )

        validation = IntentValidator.validate(
            plan.operation,
            [plan.target_column] if plan.target_column else [],
        )

        print("=" * 60)
        print("Question          :", question)
        print("Operation         :", plan.operation)
        print(
            "Matched Columns   :",
            [plan.target_column.name] if plan.target_column else [],
        )
        print("Validation        :", validation.success)
        print("Validation Error  :", validation.error)
        print("=" * 60)

        if not validation.success:
            return (
                {
                    "success": False,
                    "error": validation.error,
                },
                None,
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

        return response, plan
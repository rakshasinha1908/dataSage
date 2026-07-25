from dotenv import load_dotenv

from backend.core.ai.ai_engine import InsightEngine
from models.insight_request import InsightRequest
from models.query_plan import QueryPlan
from models.response import Response
from models.visualization import Visualization
from models.column_schema import ColumnSchema

load_dotenv()

query_plan = QueryPlan(
    operation="mean",
    target_column=ColumnSchema(
        name="transaction_amount",
        normalized_name="transaction amount",
        data_type="float",
        sample_values=[],
    ),
)

response = Response(
    success=True,
    answer={
        "Delhi": 5345,
        "Mumbai": 5121,
        "Bangalore": 4988,
    },
    visualization=None,
)

request = InsightRequest(
    question="Why does Delhi have the highest average transaction amount?",
    query_plan=query_plan,
    response=response,
)

engine = InsightEngine()

print(engine.generate(request))
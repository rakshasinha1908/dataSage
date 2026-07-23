from fastapi import APIRouter, HTTPException

from storage.session_manager import SessionManager

from core.query_engine import QueryEngine

from models.query_context import QueryContext

router = APIRouter(
    prefix="/query",
    tags=["Query"],
)


@router.get("/")
def query_dataset(session_id: str, question: str):

    dataset = SessionManager.get(session_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid session ID.",
        )

    response, plan = QueryEngine.execute(
        dataset,
        question,
    )

    if response.get("success"):

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
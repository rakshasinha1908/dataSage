from fastapi import APIRouter, HTTPException

from storage.session_manager import SessionManager

router = APIRouter(
    prefix="/schema",
    tags=["Schema"]
)


@router.get("/{session_id}")
def get_schema(session_id: str):

    dataset = SessionManager.get(session_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )

    return {
        "session_id": dataset.session_id,
        "filename": dataset.filename,
        "columns": [
            {
                "name": column.name,
                "normalized_name": column.normalized_name,
                "dtype": column.dtype,
                "nullable": column.nullable,
                "unique_count": column.unique_count,
                "sample_values": column.sample_values
            }
            for column in dataset.schema
        ]
    }
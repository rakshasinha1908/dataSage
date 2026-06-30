from fastapi import APIRouter, UploadFile, File

from core.dataset_manager import DatasetManager
from storage.session_manager import SessionManager

router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)


@router.post("/")
def upload_dataset(file: UploadFile = File(...)):
    dataset = DatasetManager.load_dataset(
        file=file.file,
        filename=file.filename
    )

    session_id = SessionManager.save(dataset)

    return {
        "status": "success",
        "session_id": session_id,
        "filename": dataset.filename,
        "rows": len(dataset.dataframe),
        "columns": len(dataset.dataframe.columns)
    }
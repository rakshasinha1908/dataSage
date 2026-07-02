from fastapi import APIRouter, UploadFile, File

from core.dataset_manager import DatasetManager
from storage.session_manager import SessionManager
from core.schema_engine import SchemaEngine

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
    
    dataset = SchemaEngine.generate(dataset)
    session_id = SessionManager.save(dataset)

    return {
        "status": "success",
        "session_id": session_id,
        "filename": dataset.filename,
        "rows": len(dataset.dataframe),
        "columns": len(dataset.dataframe.columns),
        "schema_columns": len(dataset.schema)
    }
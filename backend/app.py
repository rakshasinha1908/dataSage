from fastapi import FastAPI
from api.upload import router as upload_router
from api.schema import router as schema_router
from api.debug import router as debug_router

app = FastAPI(
    title="DataSage API",
    version="2.0.0"
)

app.include_router(upload_router)
app.include_router(schema_router)
app.include_router(debug_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to DataSage V2 🚀"
    }
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.upload import router as upload_router
from api.schema import router as schema_router
from api.debug import router as debug_router
from api.query import router as query_router
from api.insight import router as insight_router
from api.chat import router as chat_router


# -------------------------------------------------
# Environment
# -------------------------------------------------

load_dotenv()


# -------------------------------------------------
# Application
# -------------------------------------------------

app = FastAPI(
    title="DataSage API",
    version="1.0.0",
)


# -------------------------------------------------
# CORS
# -------------------------------------------------

allowed_origins = [
    "http://localhost:5173",
]

frontend_url = os.getenv("FRONTEND_URL")

if frontend_url:
    allowed_origins.append(
        frontend_url.rstrip("/")
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------
# Routers
# -------------------------------------------------

app.include_router(upload_router)
app.include_router(schema_router)
app.include_router(debug_router)
app.include_router(query_router)
app.include_router(insight_router)
app.include_router(chat_router)


# -------------------------------------------------
# Health / Root
# -------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Welcome to DataSage🚀",
        "status": "healthy",
    }
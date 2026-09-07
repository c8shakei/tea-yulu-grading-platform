"""FastAPI backend entry point for Enshi Yulu tea grading and traceability platform."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from src.backend import database as db
from src.backend import detections, traceability
from src.backend.auth import router as auth_router
from src.backend.config import MODEL_PATH, PROJECT_ROOT
from src.backend.detections import set_detector
from src.inference.detector import TeaGradeDetector


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and detection model on startup."""
    db.init_db()
    # Load the W2 detection model once and reuse across requests.
    detector = TeaGradeDetector(weight_path=str(MODEL_PATH), device="cpu")
    set_detector(detector)
    yield


app = FastAPI(
    title="恩施玉露茶品质分级与溯源平台后端 API",
    description="W3 M3 里程碑：FastAPI + SQLite + 哈希链 + JWT 认证",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(detections.router, prefix="/api")
app.include_router(traceability.router, prefix="/api")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return unified {code, message, data} for HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Return unified {code, message, data} on unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": f"Internal error: {exc}", "data": None},
    )


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {"code": 0, "message": "ok", "data": {"status": "up"}}


@app.get("/api/ui/schema", tags=["UI"])
async def ui_schema():
    """Return low-code UI configuration JSON."""
    import json

    schema_path = PROJECT_ROOT / "src" / "backend" / "ui_schema.json"
    with schema_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {"code": 0, "message": "ok", "data": data}


# Static file access for W2 training artifacts (training curves, metrics JSON).
@app.get("/models/{filename}", tags=["Static"])
async def serve_model_asset(filename: str):
    file_path = PROJECT_ROOT / "models" / filename
    if not file_path.exists():
        return JSONResponse(status_code=404, content={"code": 404, "message": "file not found", "data": None})
    return FileResponse(file_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.backend.main:app", host="0.0.0.0", port=8000, reload=True)

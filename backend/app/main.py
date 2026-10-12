import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import CORS_ORIGINS, DEMO_DISCLAIMER
from backend.app.models.database import init_db
from backend.app.api.websocket import ws_manager
from backend.app.api.routes_profiles import router as profiles_router
from backend.app.api.routes_shipments import router as shipments_router
from backend.app.api.routes_readings import router as readings_router
from backend.app.api.routes_alerts import router as alerts_router
from backend.app.api.routes_nfc import router as nfc_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cryoursus")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CryoUrsus SQLite database and seed profiles...")
    init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("CryoUrsus Backend shutting down...")

app = FastAPI(
    title="CryoUrsus API",
    description="Explainable cold-chain monitoring simulation backend. " + DEMO_DISCLAIMER,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "http_error",
                "message": str(exc.detail),
            }
        },
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected server error occurred.",
            }
        },
    )

# Include all API routers under /api prefix
app.include_router(profiles_router, prefix="/api")
app.include_router(shipments_router, prefix="/api")
app.include_router(readings_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(nfc_router, prefix="/api")

@app.get("/api/health")
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "CryoUrsus Simulation Engine",
        "database": "ready",
        "demo_mode": True,
        "disclaimer": DEMO_DISCLAIMER,
    }

@app.websocket("/api/ws/shipments/{shipment_id}")
async def websocket_shipment_stream(websocket: WebSocket, shipment_id: str):
    await ws_manager.connect(shipment_id, websocket)
    try:
        while True:
            # Keep socket alive and allow client to ping/send commands
            data = await websocket.receive_text()
            logger.debug("Received ws data on %s: %s", shipment_id, data)
    except WebSocketDisconnect:
        ws_manager.disconnect(shipment_id, websocket)
    except Exception as e:
        logger.warning("WebSocket exception on %s: %s", shipment_id, str(e))
        ws_manager.disconnect(shipment_id, websocket)

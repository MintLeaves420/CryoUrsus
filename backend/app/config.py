import os
from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HOST: str = os.getenv("HOST", "127.0.0.1")
PORT: int = int(os.getenv("PORT", "8000"))
CORS_ORIGINS: List[str] = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]
DATABASE_PATH: Path = Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "cryoursus.db")))
SIMULATION_TICK_INTERVAL_SECONDS: float = float(os.getenv("SIMULATION_TICK_INTERVAL_SECONDS", "1.5"))
DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")

DEMO_DISCLAIMER: str = (
    "CryoUrsus Telemetry & Thermal Viability Model."
)
METHOD_VERSION: str = "demo-v1"

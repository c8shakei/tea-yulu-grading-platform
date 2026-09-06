"""Backend configuration and constants."""

import os
from datetime import timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = Path(os.getenv("TEA_DB_PATH", str(DATA_DIR / "tea_yulu.db")))
UPLOAD_DIR = PROJECT_ROOT / "uploads"

# Upload constraints
MAX_UPLOAD_SIZE = int(os.getenv("TEA_MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))  # 10 MB
MODEL_PATH = PROJECT_ROOT / "models" / "best_detect.pt"

# JWT secret: read from env, fallback to a dev-only default.
JWT_SECRET = os.getenv("TEA_JWT_SECRET", "dev-secret-change-me-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = timedelta(hours=int(os.getenv("TEA_JWT_EXPIRE_HOURS", "24")))

# Grade labels frozen by project contract.
CLASS_NAMES = ["特级", "一级", "二级", "等外"]
CLASS_MAP = {0: "特级", 1: "一级", 2: "二级", 3: "等外"}

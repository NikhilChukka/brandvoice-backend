from dotenv import load_dotenv
import os

# Load .env file from the current directory (app)
# This assumes main.py and .env are in the same directory 'app'
# or that you run the app from the 'app' directory.
# For more robust pathing if running from project root:
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import router as api_v1_router
from app.core.config import get_settings

def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title=s.app_name,
        version="1.0.0",
        description="Multi-agent content automation backend",
        docs_url="/docs", redoc_url="/redoc"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.allow_origins, allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )
    app.include_router(api_v1_router, prefix="/api/v1", tags=["v1"])
    return app

app = create_app()

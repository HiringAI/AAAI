from fastapi import FastAPI

from app.api.v1.endpoints import analysis
from app.config import settings

app = FastAPI()

app.include_router(analysis.router, prefix="/api/v1/analysis")


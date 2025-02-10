from fastapi import FastAPI

from api.v1.endpoints import analysis
from config import settings

app = FastAPI()

app.include_router(analysis.router, prefix="/api/v1/analysis")


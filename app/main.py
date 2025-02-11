from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints import analysis
from app.config import settings

app = FastAPI()

app.include_router(analysis.router, prefix="/api/v1/analysis")
app.mount("/static", StaticFiles(directory="static"), name="static")

from fastapi import FastAPI
import openai

from api.v1.endpoints import analysis
from config import settings

app = FastAPI()

# Azure OpenAI 설정
openai.api_key = settings.openai_api_key
# Azure OpenAI를 사용할 경우, 아래와 같이 설정
openai.api_type = settings.openai_api_type
openai.api_base = settings.openai_endpoint
openai.api_version = settings.openai_api_version


app.include_router(analysis.router, prefix="/api/v1/analysis")


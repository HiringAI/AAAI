from fastapi import FastAPI
import openai

from config import settings

app = FastAPI()

# Azure OpenAI 설정
openai.api_key = settings.openai_api_key
# Azure OpenAI를 사용할 경우, 아래와 같이 설정
openai.api_type = "azure"
openai.api_base = settings.openai_endpoint
openai.api_version = settings.openai_api_version

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI + Azure OpenAI!"}

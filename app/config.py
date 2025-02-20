import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    openai_endpoint: str
    openai_api_version: str
    openai_deployment: str

    azure_blob_key: str

    google_api_key: str
    google_api_deployment: str

    base_url: str
    
    port: int = 8000

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()

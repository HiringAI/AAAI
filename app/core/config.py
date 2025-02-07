from pydantic.v1 import BaseSettings


class Settings(BaseSettings):

    AI_API_URL: str = "https://skcc-dwf-hr-dev-oai-usea-01.openai.azure.com"

    class Config:
        env_file = ".env"


settings = Settings()
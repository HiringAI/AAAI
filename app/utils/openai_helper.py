from openai import AzureOpenAI
from config import settings

# Azure OpenAI 설정
agent = AzureOpenAI(
    api_version=settings.openai_api_version,
    azure_endpoint=settings.openai_endpoint,
    api_key=settings.openai_api_key
)

async def make_prompt(provided_messages, provided_temperature, provided_max_tokens):
    return agent.chat.completions.create(
            model=settings.openai_deployment,  # Azure 배포명
            messages=provided_messages,
            temperature=provided_temperature,
            max_tokens=provided_max_tokens
        )

async def extract_content(completions):
    try:
        return completions.choices[0].message.content
    except (AttributeError, IndexError) as e:
        # Handle the error or return a default value
        return f"Error: {str(e)}"
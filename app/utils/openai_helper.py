from openai import AzureOpenAI
from app.config import settings

# Azure OpenAI 설정
agent = AzureOpenAI(
    api_version=settings.openai_api_version,
    azure_endpoint=settings.openai_endpoint,
    api_key=settings.openai_api_key
)

# api 콜을 날리고 결과를 반환한다.
async def make_prompt(provided_messages, provided_temperature, provided_max_tokens):
    return agent.chat.completions.create(
            model=settings.openai_deployment,  # Azure 배포명
            messages=provided_messages,
            temperature=provided_temperature,
            max_tokens=provided_max_tokens
        )

# completions 속 llm 의 반환 메시지만 추출한다.
def extract_content(completions):
    try:
        return completions.choices[0].message.content
    except (AttributeError, IndexError) as e:
        return f"Error: {str(e)}"
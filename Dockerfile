# 베이스 이미지 설정 (Python 3.9 예시)
FROM python:3.10-slim

# 작업 디렉토리 생성
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY ./app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# 소스 코드 복사
COPY ./app /app

# 8000 포트 개방
EXPOSE 8000

# FastAPI 실행 명령 (uvicorn)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

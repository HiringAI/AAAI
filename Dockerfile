# 베이스 이미지 설정
FROM python:3.10-slim

# libgl, ffmpeg 다운로드
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# 작업 디렉토리 생성
WORKDIR /

# /static 디렉토리 생성
RUN mkdir -p /static

# 의존성 파일 복사 및 설치
COPY ./app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# 소스 코드 복사
COPY ./app /app

# 8000 포트 개방
EXPOSE 8000

# FastAPI 실행 명령 (uvicorn)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

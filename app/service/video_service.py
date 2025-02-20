import os
import cv2
from fastapi import HTTPException
import uuid
import io
import asyncio
import subprocess

from azure.storage.blob import BlobServiceClient, PublicAccess
import google.generativeai as genai

from app.utils.openai_helper import make_prompt, extract_content
from app.utils.openai_message import OpenAIMessage

from app.config import settings

# gemini 설정
genai.configure(api_key=settings.google_api_key)

# Create the BlobServiceClient object
blob_service_client = BlobServiceClient.from_connection_string(settings.azure_blob_key)

async def upload_image_to_azure(frame, container_name, image_filename):
    try:
        _, buffer = cv2.imencode(".jpg", frame)
        image_bytes = io.BytesIO(buffer.tobytes())
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=image_filename)        
        blob_client.upload_blob(image_bytes)
    except ResourceExistsError:
        print(f"이미 존재하는 파일: {image_filename}")
    except Exception as e:
        print(f"Azure 업로드 오류: {e}")

async def slicing_video(video_content: bytes, filename: str):
    id = str(uuid.uuid4())
    static_folder = f"static/videos/{id}"

    os.makedirs(static_folder, exist_ok=True)
    
    video_path = os.path.join(static_folder, filename)

    try:
        with open(video_path, "wb") as f:
            f.write(video_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"동영상 저장 중 오류: {str(e)}")

    static_images = f"static/images/{id}"
    os.makedirs(static_images, exist_ok=True)

    container_name = id
    blob_service_client.create_container(container_name, public_access=PublicAccess.container)

    # Use ffmpeg to extract frames
    frame_pattern = os.path.join(static_images, "frame_%04d.jpg")
    ffmpeg_command = [
        "ffmpeg", "-i", video_path, "-vf", "fps=20", frame_pattern
    ]

    try:
        subprocess.run(ffmpeg_command, check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"ffmpeg 실행 오류: {str(e)}")

    tasks = []
    for frame_filename in os.listdir(static_images):
        frame_path = os.path.join(static_images, frame_filename)
        tasks.append(upload_image_to_azure(frame=cv2.imread(frame_path), container_name=id, image_filename=frame_filename))
    
    await asyncio.gather(*tasks)

    return id


async def analyze_slice_image(id: str):
    image_url_list = []
    results = []

    file_count = len(os.listdir(f"static/images/{id}"))

    for i in range(file_count):
        image_url_list.append(f"{settings.base_url}/{id}/frame_{i}.jpg")
        if len(image_url_list) == 20:
            try:
                message = OpenAIMessage()
                for image_url in image_url_list:
                    message.add_user_message(message_type="image_url", content=image_url)

                message.add_user_message(message_type="text", content="이 사진들을 분석해줘")

                llm_response = await make_prompt(message.get_messages(), 0.7, 100)
                
                results.append(extract_content(llm_response))
                image_url_list = []
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"AI API 호출 오류: {str(e)}")

    return {"detail": "동영상 처리 및 이미지 전송 완료", "results": results}


async def whole_video(video_content: bytes, filename: str):

    # 1. 고유 ID 생성
    id = str(uuid.uuid4())

    # 2. 동영상 파일 저장할 로컬 폴더 생성, 경로 저장
    video_folder = f"static/videos/{id}"
    if not os.path.exists(video_folder):
        os.makedirs(video_folder)

    video_path = os.path.join(video_folder, "video.mp4")

    # 3. 바이너리 모드로 동영상 저장
    try:
        with open(video_path, "wb") as f:
            f.write(video_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"동영상 저장 중 오류: {str(e)}")

    # 4. Azure Blob Storage 클라이언트 초기화
    try:
        blob_service_client = BlobServiceClient.from_connection_string(settings.azure_blob_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"클라이언트 초기화 오류: {str(e)}")

    # 5. 고유 ID를 컨테이너 이름으로 사용하여 새 컨테이너 생성
    try:
        container_client = blob_service_client.create_container(id, public_access=PublicAccess.container)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blob컨테이너 생성 오류: {str(e)}")

    # 6. 동영상 파일을 컨테이너에 업로드
    try:
        blob_client = blob_service_client.get_blob_client(container=id, blob="video.mp4")
        with open(video_path, "rb") as data:
            blob_client.upload_blob(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"동영상 업로드 오류: {str(e)}")

    return id


async def analyze_video(id: str):
    # 1. 동영상 URL 구성 (Azure Blob Storage에 업로드된 URL)
    video_url = f"static/videos/{id}/video.mp4"

    # Upload the video.
    video_file = genai.upload_file(path=video_url)

    # Check whether the file is ready to be used.
    while video_file.state.name == "PROCESSING":
        await asyncio.sleep(10)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError(video_file.state.name)

    # Choose a Gemini model.
    model = genai.GenerativeModel(model_name=settings.google_api_deployment)

    # Prompt
    full_prompt = "이 비디오를 분석해줘"

    # Make the LLM request.
    print("Making LLM inference request...")
    response = model.generate_content([video_file, full_prompt], request_options={"timeout": 10000})

    return {"detail": "동영상 분석 완료", "result": response.text}

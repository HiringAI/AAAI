import os
import cv2
from fastapi import HTTPException
import uuid
import io
import asyncio
import subprocess

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient

from app.utils.openai_helper import make_prompt, extract_content
from app.utils.openai_message import OpenAIMessage

from app.config import settings

# Create the BlobServiceClient object
blob_service_client = BlobServiceClient.from_connection_string(settings.azure_blob_key)

# 비동기 이미지 업로드
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
    blob_service_client.create_container(container_name)

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

async def analyze_video(id: str):
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

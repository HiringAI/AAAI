import os
import cv2
from fastapi import HTTPException
from app.config import settings
import uuid
import asyncio

from azure.storage.blob import BlobServiceClient, PublicAccess
import google.generativeai as genai

from app.utils.openai_helper import make_prompt, extract_content
from app.utils.openai_message import OpenAIMessage

# gemini 설정
genai.configure(api_key=settings.google_api_key)

async def slicing_video(video_content: bytes, filename: str):
    id = str(uuid.uuid4())

    # 1. 동영상 파일을 저장할 정적 폴더 지정
    static_folder = f"static/videos/{id}"

    if not os.path.exists(static_folder):
        os.makedirs(static_folder)
    video_path = os.path.join(static_folder, filename)

    try:
        with open(video_path, "wb") as f:
            f.write(video_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"동영상 저장 중 오류: {str(e)}")

    # 2. OpenCV를 통해 동영상 파일을 염
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise HTTPException(status_code=500, detail="CV로 동영상 파일 열기 실패")

    # 3. 동영상의 FPS(초당 프레임 수)를 가져오기 -> "추출 기준을 설정" -> "어떤 프레임을 추출할지 결정하는 단꼐"
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:  # 일부 동영상은 FPS정보를 제대로 제공하지 않는 경우도 있다고 해서 추가
        fps = 30  # FPS 값을 제대로 읽지 못한 경우 기본값 30으로 설정

    sample_interval = fps / 20
    frame_index = 0  # 전체 프레임 번호
    next_frame_index = 0.0  # 다음에 추출할 프레임의 기준 번호

    # 사진 저장할 디렉터리 생성
    static_images = f"static/images/{id}"
    if not os.path.exists(static_images):
        os.makedirs(static_images)

    # Create a unique name for the container
    container_name = id

    # Create the BlobServiceClient object
    blob_service_client = BlobServiceClient.from_connection_string(settings.azure_blob_key)

    # Create the container
    container_client = blob_service_client.create_container(container_name, public_access=PublicAccess.container)

    # 4. 동영상에서 프레임을 하나씩 읽으면서 원하는 프레임만 추출 -> "실제로 프레임추출 하고 AI API로 전송"
    while True:
        ret, frame = cap.read()  # ret: 프레임 읽기 성공 여부, frame: 읽은 프레임 데이터
        if not ret:
            break  # 프레임 읽기를 종료

        # 프레임 번호가 추출해야 할 인덱스보다 크거나 같다면, 이 프레임을 추출 대상으로 함
        if frame_index >= next_frame_index:
            image_filename = f"frame_{frame_index}.jpg"
            image_path = os.path.join(static_images, image_filename)

            cv2.imwrite(image_path, frame)

            # azure 에 이미지 업로드
            try:
                blob_client = blob_service_client.get_blob_client(container=container_name, blob=image_filename)
                with open(file=image_path, mode="rb") as data:
                    blob_client.upload_blob(data)
            except Exception as e:
                print(e)

        frame_index += 1

    cap.release()

    return id


async def analyze_slice_image(id: str):
    image_url_list = []
    results = []

    file_count = len(os.listdir(os.listdir(f"static/images/{id}")))

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

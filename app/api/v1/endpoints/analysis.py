
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.service import video_service

router = APIRouter()

@router.post("/upload_video")
async def upload_video(file: UploadFile = File(...)):
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="동영상 파일이 아님")

    # 업로드된 파일 비동기로 받기
    try:
        video_content = await file.read()   # 업로드된 파일의 내용을 비동기적으로 읽음, await 키워드는 해당작업이 완료할떄 까지 기다림, 읽은 데이터는 bytes형식의 데이터
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"동영상 파일 읽기 중 오류 발생: {str(e)}")

    result = {
        "image_id": await video_service.slicing_video(video_content, file.filename),
        "video_id": await video_service.whole_video(video_content, file.filename)
    }

    return {"id" : result}


@router.post("/analyze_slice_images")
async def analyze_slice_images_endpoint(id: str):     #async 통해 비동기 함수를 나타내교 ,IO작업 처리
    result = await video_service.analyze_slice_image(id)
    return result


@router.post("/analyze_video")
async def analyze_video_endpoint(id: str):
    result = await video_service.analyze_video(id)
    return result






# from fastapi import HTTPException
#
# from config import settings
#
# import requests
#
# def analyze_video(video_content: bytes, filename: str, content_type: str):
#
#     ai_api_url = settings.AI_API_URL
#
#     files = {
#         "file" : (video_content, filename, content_type)
#     }
#
#
#
#
#
#     ########################
#
#     # 인공지능 API에 동영상 전송
#     try:
#         response = requests.post(ai_api_url, files=files)
#         response.raise_for_status()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"인공지능 API 호출 오류: {str(e)}")
#
#
#     # 결과값 수신
#     try:
#         result = response.json()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"결과값 수신중 에러 발생: {str(e)}")
#
#

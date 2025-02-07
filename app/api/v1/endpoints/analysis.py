from fastapi import APIRouter

router = APIRouter()

@router.get("")
def analysis():
    return {"message": "test"}

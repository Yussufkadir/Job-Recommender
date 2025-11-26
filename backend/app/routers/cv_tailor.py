from fastapi import APIRouter

router = APIRouter()

@router.post("/cv_tailor")
async def cv_tailor():
    return {"message": "it will handle the llm connection for cv tailoring"}
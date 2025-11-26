from fastapi import APIRouter

router = APIRouter()

@router.post("/signup")
async def signup():
    return {"message": "placeholder for sign in logic"}

@router.post("/login")
async def login():
    return {"message": "placeholder for login logic"}

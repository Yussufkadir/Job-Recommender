import re

with open("app/routers/auth.py", "r") as f:
    code = f.read()

signup_patch = """async def signup(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    print(f"SIGNUP ATTEMPT: {user.email}")"""
code = code.replace("async def signup(request: Request, user: UserCreate, db: Session = Depends(get_db)):", signup_patch)

login_patch = """async def login(request: Request, user: UserLogin, db: Session = Depends(get_db)):
    print(f"LOGIN ATTEMPT: {user.email}")
    body = await request.json()
    print(f"RAW LOGIN BODY: {body}")"""
code = code.replace("async def login(request: Request, user: UserLogin, db: Session = Depends(get_db)):", login_patch)

with open("app/routers/auth.py", "w") as f:
    f.write(code)

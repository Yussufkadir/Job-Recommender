from app.core.security import verify_password, get_password_hash
from app.models.user import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///./job_recommender.db')
Session = sessionmaker(bind=engine)
session = Session()

user = session.query(User).filter(User.email=="test@test.com").first()
if user:
    print("Testing test@test.com")
    print(verify_password("password", user.hashed_password))

user2 = session.query(User).filter(User.email=="test5@test.com").first()
if user2:
    print("Testing test5@test.com")
    print(verify_password("Password123!", user2.hashed_password))

else:
    print("Could not find test5@test.com")
    
print("New hash test:", get_password_hash("testpwd"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User

engine = create_engine('sqlite:///./job_recommender.db')
Session = sessionmaker(bind=engine)
session = Session()

users = session.query(User).all()
for u in users:
    print(f"ID: {u.id}, Email: {u.email}, Hashed_pwd: {str(u.hashed_password)[:50]}...")

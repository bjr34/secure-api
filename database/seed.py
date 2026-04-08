from database.db import engine, Base, SessionLocal, User
from passlib.context import CryptContext

Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()
user = User(username="testuser", hashed_password=pwd_context.hash("pword123"), email="test@example.com")
db.add(user)
db.commit()
db.close()

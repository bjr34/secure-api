from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "sqlite:///./secure_api.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_with_id(db: Session, user_id: int):
    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

def get_user_with_name(db: Session, username: str):
    return (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=False)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    email = Column(String, unique=True)
    
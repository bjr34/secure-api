from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database.db import get_db, get_user_with_id, User

SECRET_KEY = "your-secret-key-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class TokenData(BaseModel):
    """Pydantic model for JWT payload."""
    username: Optional[str] = None


class Token(BaseModel):
    """Response model for login endpoint."""
    access_token: str
    token_type: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    TODO: Compare plain password against bcrypt hash.
    Hint: Use pwd_context.verify()
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    TODO: Hash a plain password using bcrypt.
    Hint: Use pwd_context.hash()
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    TODO: Create a JWT token.
    Steps:
    1. Copy the input dict (don't mutate it)
    2. If expires_delta is None, set it to ACCESS_TOKEN_EXPIRE_MINUTES
    3. Calculate expiration time: datetime.utcnow() + expires_delta
    4. Add "exp" key to the copied dict
    5. Encode with jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode = to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,  # paylaod (e.g. username & exp date)
        SECRET_KEY,  # signing secret
        algorithm=ALGORITHM
    )


def decode_token(token: str) -> dict:
    """
    TODO: Decode and validate a JWT token.
    Steps:
    1. Try to decode with jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    2. Extract the "sub" (subject) claim
    3. Return TokenData(username=username)
    4. If JWTError or KeyError, return None (invalid token)
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id: str = payload.get("sub")

        if user_id is None:
            raise ValueError("Invalid token: no user_id")

        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Tokene expired")


def verify_token(token: str) -> str:
    """
    Verify token and extract user_id.

    Args:
        token: JWT token string

    Returns:
        User ID from token's "sub" claim

    Raises:
        HTTPException: If token is invalid

    Why: Simple wrapper for getting just the user_id from a token.
    """
    payload = decode_token(token)
    return payload.get("sub")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    user_id = verify_token(token)
    user = get_user_with_id(db, user_id)

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user

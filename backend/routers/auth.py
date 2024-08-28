from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from db import User
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional, Union
from pydantic import BaseModel
from db.session import SessionLocal

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()

# You should store this secret key in an environment variable
SECRET_KEY = 'your_secret_key'
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    token: str

class LoginForm(BaseModel):
    username: str
    password: str

def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

@router.post('/register', response_model=Dict[str, str], status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = generate_password_hash(user.password)
    new_user = User(username=user.username, password=hashed_password, is_admin=False)
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully!"}

@router.post('/login', response_model=Token)
async def login(form_data: LoginForm, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not check_password_hash(user.password, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_token({"user_id": user.id})
    return {"token": token}

@router.get('/verify', response_model=Dict[str, Union[str, int, bool]])
async def verify(current_user: User = Depends(get_current_user)):
    return {
        "message": "Token is valid",
        "userId": current_user.id,
        "isAdmin": current_user.is_admin,
        "isValid": True
    }

# GitHub OAuth route (you'll need to implement the OAuth flow)
@router.get('/github')
def github_auth():
    # Implement GitHub OAuth logic here
    pass

@router.get('/github/callback')
def github_callback():
    # Implement GitHub OAuth callback logic here
    pass
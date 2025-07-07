import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.models import OAuthFlowsAuthorizationCode
from pydantic import BaseModel
from typing import Optional
import jwt
from datetime import datetime, timedelta

# OAuth2PasswordBearer allows FastAPI to authenticate using OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 Login Flow
class OAuth2ClientConfig(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str
    authorization_url: str
    token_url: str

# JWT Creation Helper
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Function to decode JWT and get user info
def decode_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# OAuth2 Dependency
def get_current_user(token: str = Depends(oauth2_scheme)):
    return decode_jwt(token)

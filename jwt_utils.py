import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "my-super-secret-jwt-key-for-development-only-12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

class JWTManager:
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify JWT token and return payload"""
        try:
            print(f"🔍 JWT VERIFY: Verifying token: {token[:50]}...")
            print(f"🔍 JWT VERIFY: SECRET_KEY: {SECRET_KEY}")
            print(f"🔍 JWT VERIFY: ALGORITHM: {ALGORITHM}")
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            print(f"🔍 JWT VERIFY: Decoded payload: {payload}")
            return payload
        except jwt.ExpiredSignatureError as e:
            print(f"❌ JWT VERIFY: Token expired: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError as e:
            print(f"❌ JWT VERIFY: JWT error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        except Exception as e:
            print(f"❌ JWT VERIFY: Unexpected error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    @staticmethod
    def get_current_user_from_token(token: str) -> Dict[str, Any]:
        """Extract current user from JWT token"""
        payload = JWTManager.verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        return payload
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

# Dependency for protected routes
async def get_current_hr_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dependency to get current HR user from JWT token"""
    print(f"🔍 JWT AUTH: Received credentials: {credentials}")
    token = credentials.credentials
    print(f"🔍 JWT AUTH: Token: {token[:50]}...")
    payload = JWTManager.get_current_user_from_token(token)
    print(f"🔍 JWT AUTH: Payload: {payload}")
    
    # Check if user is HR admin
    if payload.get("role") != "hr_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return payload

# Optional dependency for routes that can work with or without authentication
async def get_optional_current_hr_user(credentials: Optional[HTTPAuthorizationCredentials] = None) -> Optional[Dict[str, Any]]:
    """Optional dependency to get current HR user from JWT token"""
    if not credentials:
        return None
    
    try:
        return await get_current_hr_user(credentials)
    except HTTPException:
        return None


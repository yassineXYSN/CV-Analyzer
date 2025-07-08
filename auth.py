import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from models import User, UserSession
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REMEMBER_ME_EXPIRE_DAYS = 30

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def create_session_token() -> str:
    """Create a secure session token"""
    return secrets.token_urlsafe(32)

def create_user_session(db: Session, user_id: int, remember_me: bool = False) -> str:
    """Create a user session"""
    session_token = create_session_token()
    expires_at = datetime.utcnow() + timedelta(days=REMEMBER_ME_EXPIRE_DAYS if remember_me else 1)
    
    # Remove old sessions for this user
    db.query(UserSession).filter(UserSession.user_id == user_id).delete()
    
    # Create new session
    session = UserSession(
        user_id=user_id,
        session_token=session_token,
        expires_at=expires_at,
        is_remember_me=remember_me
    )
    db.add(session)
    db.commit()
    
    return session_token

def get_user_from_session(db: Session, session_token: str) -> Optional[User]:
    """Get user from session token"""
    session = db.query(UserSession).filter(
        UserSession.session_token == session_token,
        UserSession.expires_at > datetime.utcnow()
    ).first()
    
    if session:
        return db.query(User).filter(User.id == session.user_id).first()
    return None

def delete_user_session(db: Session, session_token: str):
    """Delete user session (logout)"""
    db.query(UserSession).filter(UserSession.session_token == session_token).delete()
    db.commit()

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_user(db: Session, email: str, password: str, first_name: str, last_name: str) -> User:
    """Create a new user"""
    hashed_password = hash_password(password)
    user = User(
        email=email,
        password_hash=hashed_password,
        first_name=first_name,
        last_name=last_name,
        is_active=1,
        profile_picture=None,
        is_verified=0
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

import jwt
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Union
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.auth import UserRole, TokenPayload

# Initialize Argon2id password hasher with RFC 9106 recommended parameters
_password_hasher = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
    hash_len=settings.ARGON2_HASH_LEN,
    salt_len=settings.ARGON2_SALT_LEN
)

def hash_password(password: str) -> str:
    """
    Hash a plaintext password using Argon2id with memory-hard parameters.
    Argon2id protects against GPU/ASIC brute-force attacks and side-channel timing leaks.
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    return _password_hasher.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against an Argon2id hash.
    Uses constant-time comparison in the underlying CFFI binding.
    Returns False safely on any mismatch or malformed hash without crashing.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    except Exception as e:
        logger.error(f"Unexpected error during password verification: {e}")
        return False

def check_needs_rehash(hashed_password: str) -> bool:
    """Check if the hash was created with older/weaker Argon2 parameters."""
    try:
        return _password_hasher.check_needs_rehash(hashed_password)
    except Exception:
        return True

def create_access_token(subject: str, role: Union[UserRole, str], custom_claims: Optional[Dict[str, Any]] = None) -> str:
    now = datetime.now(timezone.utc)
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    exp = int((now + expires_delta).timestamp())
    
    role_str = role.value if hasattr(role, "value") else str(role)

    payload = {
        "sub": subject,
        "role": role_str,
        "exp": exp,
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4()),
        "type": "access"
    }
    if custom_claims:
        payload.update(custom_claims)
        
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(subject: str, role: Union[UserRole, str]) -> str:
    now = datetime.now(timezone.utc)
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    exp = int((now + expires_delta).timestamp())
    
    role_str = role.value if hasattr(role, "value") else str(role)

    payload = {
        "sub": subject,
        "role": role_str,
        "exp": exp,
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4()),
        "type": "refresh"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> TokenPayload:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    return TokenPayload(
        sub=payload["sub"],
        role=UserRole(payload["role"]),
        exp=payload["exp"],
        iat=payload["iat"],
        type=payload["type"]
    )

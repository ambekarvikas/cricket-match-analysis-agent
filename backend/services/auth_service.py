from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from backend.db.database import get_db_session
from backend.db.models import User

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-dev-secret-key-to-at-least-32-characters")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "720"))
_PASSWORD_ITERATIONS = 120_000
_bearer_scheme = HTTPBearer(auto_error=False)


def _normalize_email(email: str) -> str:
    normalized = (email or "").strip().lower()
    if not normalized or "@" not in normalized:
        raise ValueError("A valid email is required.")
    return normalized


def _validate_password(password: str) -> None:
    if len(password or "") < 8:
        raise ValueError("Password must be at least 8 characters long.")


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PASSWORD_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        _PASSWORD_ITERATIONS,
        base64.b64encode(salt).decode("utf-8"),
        base64.b64encode(digest).decode("utf-8"),
    )


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        _, iteration_text, salt_text, digest_text = password_hash.split("$", 3)
        iterations = int(iteration_text)
        salt = base64.b64decode(salt_text.encode("utf-8"))
        expected = base64.b64decode(digest_text.encode("utf-8"))
    except Exception:
        return False

    calculated = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(calculated, expected)


def _serialize_user(user: User) -> Dict[str, Any]:
    return {
        "id": int(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "created_at": user.created_at.isoformat(timespec="seconds") if user.created_at else None,
    }


def create_access_token(user: Dict[str, Any]) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRY_MINUTES)
    payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "display_name": user.get("display_name"),
        "exp": expires_at,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def register_user(email: str, password: str, display_name: Optional[str] = None) -> Dict[str, Any]:
    normalized_email = _normalize_email(email)
    _validate_password(password)

    with get_db_session() as db:
        existing = db.scalar(select(User).where(User.email == normalized_email))
        if existing is not None:
            raise ValueError("A user with this email already exists.")

        user = User(
            email=normalized_email,
            display_name=(display_name or "").strip() or None,
            password_hash=_hash_password(password),
        )
        db.add(user)
        db.flush()
        return _serialize_user(user)


def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    normalized_email = _normalize_email(email)
    _validate_password(password)

    with get_db_session() as db:
        user = db.scalar(select(User).where(User.email == normalized_email))
        if user is None or not _verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password.")
        return _serialize_user(user)


def register_and_issue_token(email: str, password: str, display_name: Optional[str] = None) -> Dict[str, Any]:
    user = register_user(email=email, password=password, display_name=display_name)
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": user,
    }


def login_and_issue_token(email: str, password: str) -> Dict[str, Any]:
    user = authenticate_user(email=email, password=password)
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": user,
    }


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with get_db_session() as db:
        user = db.get(User, user_id)
        return _serialize_user(user) if user is not None else None


def _decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.") from exc


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[Dict[str, Any]]:
    if credentials is None or not credentials.credentials:
        return None

    payload = _decode_token(credentials.credentials)
    user_id = int(payload.get("sub") or 0)
    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject.")

    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists.")
    return user


def get_current_user(
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return current_user

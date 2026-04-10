from __future__ import annotations

import asyncio
import logging
from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from backend.api.schemas.auth import AuthResponse, AuthUser, LoginRequest, RegisterRequest
from backend.services.auth_service import get_current_user, login_and_issue_token, register_and_issue_token

logger = logging.getLogger("cricket_agent.api.auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    responses={400: {"description": "Registration failed."}, 500: {"description": "Registration failed."}},
)
async def register_endpoint(request: RegisterRequest) -> Dict[str, Any]:
    try:
        return await asyncio.to_thread(
            register_and_issue_token,
            request.email,
            request.password,
            request.display_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Registration endpoint failed")
        raise HTTPException(status_code=500, detail="Registration failed.") from exc


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={401: {"description": "Login failed."}, 500: {"description": "Login failed."}},
)
async def login_endpoint(request: LoginRequest) -> Dict[str, Any]:
    try:
        return await asyncio.to_thread(login_and_issue_token, request.email, request.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Login endpoint failed")
        raise HTTPException(status_code=500, detail="Login failed.") from exc


@router.get("/me", response_model=AuthUser, responses={401: {"description": "Authentication required."}})
async def me_endpoint(
    current_user: Annotated[Dict[str, Any], Depends(get_current_user)],
) -> Dict[str, Any]:
    return current_user

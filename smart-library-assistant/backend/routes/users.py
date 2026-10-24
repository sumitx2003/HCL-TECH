
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from backend.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from backend.database import get_connection

router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer_scheme = HTTPBearer()


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    course: str | None = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(bearer_scheme)
    ],
):
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, full_name, email, role, course, is_active,
                   created_at, updated_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    if row is None or not row["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or inactive",
        )

    return dict(row)


def require_librarian(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    if current_user["role"] != "librarian":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Librarian access required",
        )
    return current_user



@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest):
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ? COLLATE NOCASE",
            (str(data.email),),
        ).fetchone()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )

        try:
            cursor = conn.execute(
                """
                INSERT INTO users
                    (full_name, email, password_hash, role, course, is_active)
                VALUES (?, ?, ?, 'student', ?, 1)
                """,
                (
                    data.full_name.strip(),
                    str(data.email).lower(),
                    hash_password(data.password),
                    data.course,
                ),
            )
            conn.commit()

            return {
                "message": "Student registered successfully",
                "user_id": cursor.lastrowid,
            }

        except Exception:
            conn.rollback()
            raise


@router.post("/login")
def login(data: LoginRequest):
    with get_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? COLLATE NOCASE",
            (str(data.email),),
        ).fetchone()

    if (
        user is None
        or not user["is_active"]
        or not verify_password(data.password, user["password_hash"])
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password, or account inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user["id"], user["role"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 1800,
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
        },
    }


@router.get("/me")
def get_me(current_user: Annotated[dict, Depends(get_current_user)]):
    return current_user

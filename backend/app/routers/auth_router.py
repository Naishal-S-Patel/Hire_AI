"""
Auth router — User signup, login, Google OAuth2, and token refresh.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.user import User
from app.schemas.auth_schema import (
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    TokenPayload,
    UserOut,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# ── Password hashing ─────────────────────────────────────
# Use pbkdf2_sha256 to avoid bcrypt's 72-byte password limit while still
# keeping a strong, industry-standard hash function.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── Token helpers ─────────────────────────────────────────


def _create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str) -> str:
    return _create_token(
        {"sub": subject, "type": "access"},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        {"sub": subject, "type": "refresh"},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def verify_token(token: str, expected_type: str = "access") -> str:
    """Decode a JWT and return the subject. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != expected_type:
            raise HTTPException(status_code=401, detail="Invalid token type")
        sub: str | None = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return sub
    except JWTError:
        raise HTTPException(status_code=401, detail="Token validation failed")


# ── Signup ────────────────────────────────────────────────


@router.post("/signup", response_model=TokenPayload, status_code=201, summary="Register a new user")
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a new user account with email and password.
    Returns JWT tokens on success.
    """
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        auth_provider="local",
        role=getattr(body, 'role', 'USER'),  # Default to USER if not specified
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return TokenPayload(
        access_token=create_access_token(user.email),
        refresh_token=create_refresh_token(user.email),
    )


# ── Login ─────────────────────────────────────────────────


@router.post("/login", response_model=TokenPayload, summary="Email/password login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login with email and password. Returns JWT tokens.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return TokenPayload(
        access_token=create_access_token(user.email),
        refresh_token=create_refresh_token(user.email),
    )


# ── Google OAuth2 ─────────────────────────────────────────


@router.get("/google/login", summary="Redirect to Google OAuth2")
async def google_login():
    """Redirects the user to Google's OAuth2 consent screen."""
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback", summary="Google OAuth2 callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """
    Handles the Google OAuth2 callback.
    Creates user if doesn't exist, then redirects to frontend with tokens.
    """
    import httpx

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Google token exchange failed")

        google_tokens = token_resp.json()
        access_token = google_tokens.get("access_token")

        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch Google user info")

        user_data = user_resp.json()

    email = user_data.get("email", "")
    name = user_data.get("name", "")
    picture = user_data.get("picture", "")

    # Create or update user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            email=email,
            full_name=name,
            picture=picture,
            auth_provider="google",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update existing user's picture if changed
        if user.picture != picture:
            user.picture = picture
            await db.commit()

    # Create JWT tokens
    jwt_access_token = create_access_token(email)
    jwt_refresh_token = create_refresh_token(email)
    
    # Redirect to frontend with tokens in URL
    frontend_url = f"http://localhost:5173/auth/google/callback?access_token={jwt_access_token}&refresh_token={jwt_refresh_token}"
    return RedirectResponse(url=frontend_url, status_code=302)


# ── Refresh ───────────────────────────────────────────────


@router.post("/refresh", response_model=TokenPayload, summary="Refresh access token")
async def refresh(body: RefreshRequest):
    """Exchange a valid refresh token for a new token pair."""
    subject = verify_token(body.refresh_token, expected_type="refresh")
    return TokenPayload(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


# ── Get Current User ──────────────────────────────────────


async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency to get the currently authenticated user."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    # Verify token and get email
    email = verify_token(token, expected_type="access")
    
    # Fetch user from database
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.get("/me", response_model=UserOut, summary="Get current user")
async def get_me(user: User = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        picture=user.picture,
        auth_provider=user.auth_provider,
        role=user.role,
        created_at=user.created_at,
    )

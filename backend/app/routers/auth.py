"""
Minimal auth helpers. In production the frontend obtains a token from Keycloak
and the backend validates the JWT (or uses the Keycloak introspection endpoint).
This scaffold accepts a Bearer token and extracts the preferred_username claim
for demonstration. Replace with proper JWT validation against Keycloak JWKS.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional
import httpx
from app.core.config import settings

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Development-friendly auth.
    - If no token → treat as anonymous 'dev-user' (convenient for local testing).
    - If token present → decode without full signature check (replace in prod).
    """
    if credentials is None:
        return {"preferred_username": "dev-user", "sub": "dev-user", "roles": ["analyst"]}

    token = credentials.credentials
    try:
        # In production: fetch JWKS from Keycloak and verify signature + audience
        payload = jwt.get_unverified_claims(token)
        return {
            "preferred_username": payload.get("preferred_username", payload.get("sub", "unknown")),
            "sub": payload.get("sub"),
            "roles": payload.get("realm_access", {}).get("roles", []),
            "email": payload.get("email"),
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return user

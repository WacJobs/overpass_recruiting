from fastapi import Header, HTTPException

from app.core.config import get_settings

settings = get_settings()


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    """
    If ADMIN_API_KEY is configured, require it on admin endpoints.
    If left blank in local development, admin endpoints remain open.
    """
    if settings.admin_api_key and x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing X-Admin-Key header.")

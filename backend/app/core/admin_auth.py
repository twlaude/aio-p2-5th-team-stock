import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import settings

_security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(_security)) -> None:
    valid_username = secrets.compare_digest(credentials.username, settings.admin_username)
    valid_password = secrets.compare_digest(credentials.password, settings.admin_password)
    if not (valid_username and valid_password):
        raise HTTPException(
            status_code=401,
            detail="관리자 인증이 필요하다.",
            headers={"WWW-Authenticate": "Basic"},
        )

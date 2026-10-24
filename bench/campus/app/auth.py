from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
bearer_scheme = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials=Depends(bearer_scheme), db: Session=Depends(get_db)) -> User:
    user = db.get(User, credentials.credentials)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')
    return user

def require_role(role: str):

    def checker(current_user: User=Depends(get_current_user)) -> User:
        if current_user.role != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Forbidden')
        return current_user
    return checker

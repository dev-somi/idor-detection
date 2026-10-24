from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import UserProfile
router = APIRouter(tags=['users'])

@router.get('/users/{user_id}/profile', response_model=UserProfile)
def get_user_profile(user_id: str, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    return user

@router.get('/me/profile', response_model=UserProfile)
def get_my_profile(current_user: User=Depends(get_current_user)):
    return current_user

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.database import get_db
from app.models import ClubPost, User
from app.schemas import ClubPostCreate, ClubPostOut, ClubPostUpdate
router = APIRouter(tags=['clubs'])

@router.get('/clubs/posts/{post_id}', response_model=ClubPostOut)
def get_club_post(post_id: str, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    post = db.get(ClubPost, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail='Post not found')
    return post

@router.post('/clubs/posts', response_model=ClubPostOut)
def create_club_post(payload: ClubPostCreate, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    post = ClubPost(id=str(uuid.uuid4()), club_name=payload.club_name, author_id=current_user.id, title=payload.title, body=payload.body)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

@router.put('/clubs/posts/{post_id}', response_model=ClubPostOut)
def update_club_post(post_id: str, payload: ClubPostUpdate, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    post = db.get(ClubPost, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail='Post not found')
    if post.author_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail='Forbidden')
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(post, field, value)
    db.commit()
    db.refresh(post)
    return post

@router.delete('/clubs/posts/{post_id}')
def delete_club_post(post_id: str, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    post = db.get(ClubPost, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail='Post not found')
    db.delete(post)
    db.commit()
    return {'detail': 'Post deleted'}

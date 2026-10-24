import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import Notice, User
from app.schemas import NoticeCreate, NoticeOut
router = APIRouter(tags=['admin'])

@router.post('/admin/notices', response_model=NoticeOut)
def create_notice(payload: NoticeCreate, current_user: User=Depends(require_role('admin')), db: Session=Depends(get_db)):
    notice = Notice(id=str(uuid.uuid4()), author_id=current_user.id, title=payload.title, body=payload.body)
    db.add(notice)
    db.commit()
    db.refresh(notice)
    return notice

@router.get('/notices', response_model=list[NoticeOut])
def list_notices(current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    notices = db.query(Notice).order_by(Notice.created_at.desc()).all()
    return notices

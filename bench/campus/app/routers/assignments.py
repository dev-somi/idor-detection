from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.database import get_db
from app.models import Submission, User
from app.schemas import SubmissionOut
router = APIRouter(tags=['assignments'])

@router.get('/assignments/submissions/{submission_id}', response_model=SubmissionOut)
def get_submission(submission_id: str, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail='Submission not found')
    return submission

@router.get('/me/assignments/submissions', response_model=list[SubmissionOut])
def get_my_submissions(current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    submissions = db.query(Submission).filter(Submission.owner_id == current_user.id).all()
    return submissions

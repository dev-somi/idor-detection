from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import EnrollmentOut, SubmissionOut
from app.services.records import build_transcript, fetch_enrollment, fetch_submission, list_course_assignments
router = APIRouter(tags=['academics'])

@router.get('/enrollments/{enrollment_id}', response_model=EnrollmentOut)
def get_enrollment(enrollment_id: str, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    return fetch_enrollment(db, current_user, enrollment_id)

@router.get('/submissions/{submission_id}/feedback', response_model=SubmissionOut)
def get_submission_feedback(submission_id: str, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    return fetch_submission(db, current_user, submission_id)

@router.get('/students/{student_id}/transcript', response_model=list[EnrollmentOut])
def get_transcript(student_id: str, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    return build_transcript(db, current_user, student_id)

@router.get('/courses/{course_id}/assignments')
def get_course_assignments(course_id: str, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    return list_course_assignments(db, course_id)

from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import Appointment, Assignment, Enrollment, FileRecord, Submission, User
from app.services.access import ensure_participant, ensure_profile_visible

def fetch_enrollment(db: Session, current_user: User, enrollment_id: str) -> Enrollment:
    enrollment = db.get(Enrollment, enrollment_id)
    if enrollment is None or enrollment.student_id != current_user.id:
        raise HTTPException(status_code=404, detail='Enrollment not found')
    return enrollment

def fetch_submission(db: Session, current_user: User, submission_id: str) -> Submission:
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail='Submission not found')
    return submission

def load_file(db: Session, file_id: str) -> FileRecord:
    file_record = db.get(FileRecord, file_id)
    if file_record is None:
        raise HTTPException(status_code=404, detail='File not found')
    return file_record

def get_appointment_detail(db: Session, current_user: User, appointment_id: str) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail='Appointment not found')
    ensure_participant(current_user, appointment)
    return appointment

def build_transcript(db: Session, current_user: User, student_id: str) -> list[Enrollment]:
    student = db.get(User, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail='Student not found')
    ensure_profile_visible(current_user, student)
    return db.query(Enrollment).filter(Enrollment.student_id == student.id).all()

def list_course_assignments(db: Session, course_id: str) -> list[dict]:
    assignments = db.query(Assignment).filter(Assignment.course_id == course_id).all()
    return [{'id': a.id, 'title': a.title, 'due_date': a.due_date} for a in assignments]

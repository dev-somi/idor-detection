from fastapi import HTTPException

from app.models import Appointment, FileRecord, User


def can_modify_file(user: User, file_record: FileRecord) -> bool:
    return file_record.owner_id == user.id


def ensure_participant(user: User, appointment: Appointment) -> None:
    if user.id not in (appointment.student_id, appointment.professor_id):
        raise HTTPException(status_code=403, detail="Forbidden")


def ensure_profile_visible(viewer: User, student: User) -> None:
    if viewer.role != "admin" and viewer.department != student.department:
        raise HTTPException(status_code=403, detail="Forbidden")

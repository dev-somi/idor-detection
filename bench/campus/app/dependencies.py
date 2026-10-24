from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.database import get_db
from app.models import Appointment, FileRecord, User

def get_accessible_file(file_id: str, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)) -> FileRecord:
    file_record = db.get(FileRecord, file_id)
    if file_record is None:
        raise HTTPException(status_code=404, detail='File not found')
    if file_record.visibility != 'public' and file_record.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail='Forbidden')
    return file_record

def get_appointment_for_user(appointment_id: str, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail='Appointment not found')
    return appointment

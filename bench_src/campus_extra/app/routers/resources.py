from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.dependencies import get_accessible_file, get_appointment_for_user
from app.models import Appointment, FileRecord, User
from app.schemas import AppointmentOut, AppointmentUpdate, FileOut
from app.services.access import can_modify_file
from app.services.records import get_appointment_detail, load_file

router = APIRouter(tags=["resources"])


@router.get("/files/{file_id}/meta", response_model=FileOut)
def get_file_meta(file_record: FileRecord = Depends(get_accessible_file)):
    return file_record


@router.delete("/files/{file_id}")
def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file_record = load_file(db, file_id)
    can_modify_file(current_user, file_record)
    db.delete(file_record)
    db.commit()
    return {"detail": "File deleted"}


@router.get("/appointments/{appointment_id}", response_model=AppointmentOut)
def get_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_appointment_detail(db, current_user, appointment_id)


@router.patch("/appointments/{appointment_id}", response_model=AppointmentOut)
def patch_appointment(
    payload: AppointmentUpdate,
    appointment: Appointment = Depends(get_appointment_for_user),
    db: Session = Depends(get_db),
):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(appointment, field, value)
    db.commit()
    db.refresh(appointment)
    return appointment

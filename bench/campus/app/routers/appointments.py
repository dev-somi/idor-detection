from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.database import get_db
from app.models import Appointment, User
from app.schemas import AppointmentOut, AppointmentUpdate
router = APIRouter(tags=['appointments'])

@router.put('/appointments/{appointment_id}', response_model=AppointmentOut)
def update_appointment(appointment_id: str, payload: AppointmentUpdate, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail='Appointment not found')
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(appointment, field, value)
    db.commit()
    db.refresh(appointment)
    return appointment

@router.get('/me/appointments', response_model=list[AppointmentOut])
def get_my_appointments(current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    appointments = db.query(Appointment).filter((Appointment.student_id == current_user.id) | (Appointment.professor_id == current_user.id)).all()
    return appointments

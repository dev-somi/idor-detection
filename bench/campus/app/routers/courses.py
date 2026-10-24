from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.database import get_db
from app.models import Course, Enrollment, User
from app.schemas import CourseOut, EnrollmentOut
router = APIRouter(tags=['courses'])

@router.get('/students/{student_id}/courses', response_model=list[EnrollmentOut])
def get_student_courses(student_id: str, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    enrollments = db.query(Enrollment).filter(Enrollment.student_id == student_id).all()
    return enrollments

@router.get('/me/courses', response_model=list[EnrollmentOut])
def get_my_courses(current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    enrollments = db.query(Enrollment).filter(Enrollment.student_id == current_user.id).all()
    return enrollments

@router.get('/courses/{course_id}', response_model=CourseOut)
def get_course(course_id: str, current_user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail='Course not found')
    return course

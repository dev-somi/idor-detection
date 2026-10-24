from datetime import datetime
from pydantic import BaseModel

class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    role: str
    department: str

    class Config:
        from_attributes = True

class CourseOut(BaseModel):
    id: str
    code: str
    title: str
    professor_id: str

    class Config:
        from_attributes = True

class EnrollmentOut(BaseModel):
    id: str
    course_id: str
    semester: str
    grade: str

    class Config:
        from_attributes = True

class SubmissionOut(BaseModel):
    id: str
    assignment_id: str
    owner_id: str
    content: str
    score: str

    class Config:
        from_attributes = True

class AppointmentOut(BaseModel):
    id: str
    student_id: str
    professor_id: str
    scheduled_at: str
    topic: str
    status: str

    class Config:
        from_attributes = True

class AppointmentUpdate(BaseModel):
    scheduled_at: str | None = None
    topic: str | None = None
    status: str | None = None

class ClubPostOut(BaseModel):
    id: str
    club_name: str
    author_id: str
    title: str
    body: str
    created_at: datetime

    class Config:
        from_attributes = True

class ClubPostCreate(BaseModel):
    club_name: str
    title: str
    body: str

class ClubPostUpdate(BaseModel):
    title: str | None = None
    body: str | None = None

class FileOut(BaseModel):
    id: str
    filename: str
    visibility: str

    class Config:
        from_attributes = True

class FileDownloadOut(BaseModel):
    id: str
    filename: str
    content: str
    visibility: str

    class Config:
        from_attributes = True

class NoticeOut(BaseModel):
    id: str
    author_id: str
    title: str
    body: str
    created_at: datetime

    class Config:
        from_attributes = True

class NoticeCreate(BaseModel):
    title: str
    body: str

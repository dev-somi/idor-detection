from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    department: Mapped[str] = mapped_column(String, default='')

class Course(Base):
    __tablename__ = 'courses'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    code: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    professor_id: Mapped[str] = mapped_column(ForeignKey('users.id'))

class Enrollment(Base):
    __tablename__ = 'enrollments'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    course_id: Mapped[str] = mapped_column(ForeignKey('courses.id'))
    semester: Mapped[str] = mapped_column(String, default='2026-1')
    grade: Mapped[str] = mapped_column(String, default='')

class Assignment(Base):
    __tablename__ = 'assignments'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    course_id: Mapped[str] = mapped_column(ForeignKey('courses.id'))
    title: Mapped[str] = mapped_column(String)
    due_date: Mapped[str] = mapped_column(String, default='')

class Submission(Base):
    __tablename__ = 'submissions'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    assignment_id: Mapped[str] = mapped_column(ForeignKey('assignments.id'))
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    content: Mapped[str] = mapped_column(String)
    score: Mapped[str] = mapped_column(String, default='')

class Appointment(Base):
    __tablename__ = 'appointments'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    professor_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    scheduled_at: Mapped[str] = mapped_column(String)
    topic: Mapped[str] = mapped_column(String, default='')
    status: Mapped[str] = mapped_column(String, default='scheduled')

class ClubPost(Base):
    __tablename__ = 'club_posts'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    club_name: Mapped[str] = mapped_column(String)
    author_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    title: Mapped[str] = mapped_column(String)
    body: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class FileRecord(Base):
    __tablename__ = 'files'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    filename: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    visibility: Mapped[str] = mapped_column(String, default='private')

class Notice(Base):
    __tablename__ = 'notices'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    author_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    title: Mapped[str] = mapped_column(String)
    body: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

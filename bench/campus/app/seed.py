from datetime import datetime
from sqlalchemy.orm import Session
from app.database import Base, SessionLocal, engine
from app.models import Appointment, Assignment, ClubPost, Course, Enrollment, FileRecord, Notice, Submission, User

def _seed_data(db: Session) -> None:
    users = [User(id='student1', name='Student One', email='student1@campus.edu', role='student', department='CS'), User(id='student2', name='Student Two', email='student2@campus.edu', role='student', department='CS'), User(id='student3', name='Student Three', email='student3@campus.edu', role='student', department='EE'), User(id='professor1', name='Professor One', email='professor1@campus.edu', role='professor', department='CS'), User(id='admin1', name='Admin One', email='admin1@campus.edu', role='admin', department='Administration')]
    db.add_all(users)
    courses = [Course(id='course1', code='CS101', title='Intro to Programming', professor_id='professor1'), Course(id='course2', code='CS102', title='Data Structures', professor_id='professor1'), Course(id='course3', code='SEC301', title='Applied Security', professor_id='professor1')]
    db.add_all(courses)
    enrollments = [Enrollment(id='enroll1', student_id='student1', course_id='course1', semester='2026-1', grade='A'), Enrollment(id='enroll2', student_id='student1', course_id='course3', semester='2026-1', grade='B+'), Enrollment(id='enroll3', student_id='student2', course_id='course2', semester='2026-1', grade='A-'), Enrollment(id='enroll4', student_id='student3', course_id='course1', semester='2026-1', grade='B')]
    db.add_all(enrollments)
    assignments = [Assignment(id='assignment1', course_id='course1', title='Homework 1', due_date='2026-04-01'), Assignment(id='assignment2', course_id='course2', title='Homework 1', due_date='2026-04-05')]
    db.add_all(assignments)
    submissions = [Submission(id='submission1', assignment_id='assignment1', owner_id='student1', content="print('hello')", score='90'), Submission(id='submission2', assignment_id='assignment2', owner_id='student2', content='def solve(): pass', score='85'), Submission(id='submission3', assignment_id='assignment1', owner_id='student3', content="print('world')", score='88')]
    db.add_all(submissions)
    appointments = [Appointment(id='appointment1', student_id='student1', professor_id='professor1', scheduled_at='2026-05-01T10:00:00', topic='Career advice', status='scheduled'), Appointment(id='appointment2', student_id='student2', professor_id='professor1', scheduled_at='2026-05-02T14:00:00', topic='Research opportunities', status='scheduled')]
    db.add_all(appointments)
    posts = [ClubPost(id='post1', club_name='Robotics Club', author_id='student1', title='Welcome', body='Join us for the kickoff meeting.', created_at=datetime(2026, 3, 1)), ClubPost(id='post2', club_name='Photography Club', author_id='student2', title='Spring Exhibit', body='Submissions open now.', created_at=datetime(2026, 3, 5))]
    db.add_all(posts)
    files = [FileRecord(id='file1', owner_id='student1', filename='transcript.pdf', content='student1 transcript data', visibility='private'), FileRecord(id='file2', owner_id='student2', filename='recommendation.pdf', content='student2 recommendation letter', visibility='private'), FileRecord(id='file3', owner_id='student1', filename='syllabus_notes.pdf', content='public syllabus notes', visibility='public')]
    db.add_all(files)
    notices = [Notice(id='notice1', author_id='admin1', title='Semester Schedule', body='Classes begin March 1st.', created_at=datetime(2026, 2, 1))]
    db.add_all(notices)
    db.commit()

def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.get(User, 'student1') is None:
            _seed_data(db)
    finally:
        db.close()

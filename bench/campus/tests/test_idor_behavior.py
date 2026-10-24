from tests.conftest import auth_headers


# --- Vulnerable behavior: these describe how the API currently behaves ---


def test_idor_user_profile_cross_access(client):
    response = client.get("/users/student2/profile", headers=auth_headers("student1"))
    assert response.status_code == 200
    assert response.json()["id"] == "student2"


def test_idor_student_courses_cross_access(client):
    response = client.get("/students/student2/courses", headers=auth_headers("student1"))
    assert response.status_code == 200
    assert any(e["id"] == "enroll3" for e in response.json())


def test_idor_submission_cross_access(client):
    response = client.get("/assignments/submissions/submission2", headers=auth_headers("student1"))
    assert response.status_code == 200
    assert response.json()["owner_id"] == "student2"


def test_idor_appointment_cross_update(client):
    response = client.put(
        "/appointments/appointment2",
        headers=auth_headers("student1"),
        json={"status": "cancelled"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_idor_club_post_cross_delete(client):
    response = client.delete("/clubs/posts/post2", headers=auth_headers("student1"))
    assert response.status_code == 200

    follow_up = client.get("/clubs/posts/post2", headers=auth_headers("student1"))
    assert follow_up.status_code == 404


def test_idor_private_file_cross_download(client):
    response = client.get("/files/file2/download", headers=auth_headers("student1"))
    assert response.status_code == 200
    assert response.json()["filename"] == "recommendation.pdf"
    assert response.json()["visibility"] == "private"


# --- Safe behavior: scoped-to-self and access-controlled endpoints ---


def test_me_profile_returns_own_profile_only(client):
    response = client.get("/me/profile", headers=auth_headers("student1"))
    assert response.status_code == 200
    assert response.json()["id"] == "student1"


def test_me_courses_returns_own_enrollments_only(client):
    response = client.get("/me/courses", headers=auth_headers("student1"))
    assert response.status_code == 200
    course_ids = {e["id"] for e in response.json()}
    assert course_ids == {"enroll1", "enroll2"}


def test_me_submissions_returns_own_submissions_only(client):
    response = client.get("/me/assignments/submissions", headers=auth_headers("student2"))
    assert response.status_code == 200
    assert all(s["owner_id"] == "student2" for s in response.json())


def test_me_files_returns_own_files_only(client):
    response = client.get("/me/files", headers=auth_headers("student1"))
    assert response.status_code == 200
    filenames = {f["filename"] for f in response.json()}
    assert filenames == {"transcript.pdf", "syllabus_notes.pdf"}


def test_club_post_is_publicly_readable(client):
    response = client.get("/clubs/posts/post2", headers=auth_headers("student1"))
    assert response.status_code == 200
    assert response.json()["author_id"] == "student2"


def test_club_post_update_blocked_for_non_owner(client):
    response = client.put(
        "/clubs/posts/post2",
        headers=auth_headers("student1"),
        json={"title": "Hijacked"},
    )
    assert response.status_code == 403


def test_club_post_update_allowed_for_admin(client):
    response = client.put(
        "/clubs/posts/post2",
        headers=auth_headers("admin1"),
        json={"title": "Moderated"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Moderated"


def test_admin_notice_creation_requires_admin_role(client):
    response = client.post(
        "/admin/notices",
        headers=auth_headers("student1"),
        json={"title": "Fake notice", "body": "Not allowed"},
    )
    assert response.status_code == 403


def test_admin_notice_creation_succeeds_for_admin(client):
    response = client.post(
        "/admin/notices",
        headers=auth_headers("admin1"),
        json={"title": "Real notice", "body": "Finals begin June 1st."},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Real notice"


def test_notices_are_publicly_listable(client):
    response = client.get("/notices", headers=auth_headers("student2"))
    assert response.status_code == 200
    assert any(n["id"] == "notice1" for n in response.json())


def test_course_catalog_is_readable_by_any_authenticated_user(client):
    response = client.get("/courses/course1", headers=auth_headers("student3"))
    assert response.status_code == 200
    assert response.json()["code"] == "CS101"

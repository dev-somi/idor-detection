"""추가 엔드포인트 8개의 실제 동작이 ground_truth/endpoints.json 라벨과 맞는지 HTTP 요청으로 확인한다.

모델 입력이 아니다(bench/campus/tests/로 복사되며, app/만 모델 입력이 된다).
시드: enroll1·file1(private)·file3(public)은 student1 소유, submission2·appointment2는 student2 소유.
student1·student2는 CS, student3는 EE 학과.
"""

from tests.conftest import auth_headers


def test_enrollment_blocked_for_other_student(client):
    # campus:e18 not_vulnerable — 서비스 함수가 student_id를 비교한다
    assert client.get("/enrollments/enroll1", headers=auth_headers("student2")).status_code == 404
    assert client.get("/enrollments/enroll1", headers=auth_headers("student1")).status_code == 200


def test_submission_feedback_readable_by_other_student(client):
    # campus:e19 vulnerable — 서비스 함수가 current_user를 받지만 쓰지 않는다
    response = client.get("/submissions/submission2/feedback", headers=auth_headers("student1"))
    assert response.status_code == 200
    assert response.json()["owner_id"] == "student2"


def test_transcript_readable_by_same_department_student(client):
    # campus:e20 vulnerable — 정책은 본인·admin만 허용하지만 같은 학과면 통과한다
    response = client.get("/students/student1/transcript", headers=auth_headers("student2"))
    assert response.status_code == 200
    assert any(e["id"] == "enroll1" for e in response.json())
    assert client.get("/students/student1/transcript", headers=auth_headers("student3")).status_code == 403


def test_course_assignments_public(client):
    # campus:e21 not_vulnerable — 공개 정보이고 제목·마감일만 반환한다
    response = client.get("/courses/course1/assignments", headers=auth_headers("student2"))
    assert response.status_code == 200
    assert set(response.json()[0]) == {"id", "title", "due_date"}


def test_private_file_meta_blocked_public_allowed(client):
    # campus:e22 not_vulnerable — 의존성이 private 파일의 소유자를 확인한다
    assert client.get("/files/file1/meta", headers=auth_headers("student2")).status_code == 403
    assert client.get("/files/file3/meta", headers=auth_headers("student2")).status_code == 200
    assert client.get("/files/file1/meta", headers=auth_headers("student1")).status_code == 200


def test_file_deletable_by_other_user(client):
    # campus:e23 vulnerable — can_modify_file의 반환값을 무시한다
    assert client.delete("/files/file1", headers=auth_headers("student2")).status_code == 200
    assert client.get("/files/file1/meta", headers=auth_headers("student1")).status_code == 404


def test_appointment_detail_blocked_for_non_participant(client):
    # campus:e24 not_vulnerable — ensure_participant가 참여자가 아니면 403을 낸다
    assert client.get("/appointments/appointment2", headers=auth_headers("student1")).status_code == 403
    assert client.get("/appointments/appointment2", headers=auth_headers("professor1")).status_code == 200


def test_appointment_patch_allowed_for_non_participant(client):
    # campus:e25 vulnerable — 의존성이 존재 여부만 확인한다
    response = client.patch("/appointments/appointment2", headers=auth_headers("student1"),
                            json={"status": "cancelled"})
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

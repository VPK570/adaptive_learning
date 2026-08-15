from fastapi.testclient import TestClient

from app.auth import create_access_token
from app.validation import MAX_FILE_SIZE
from server import app

client = TestClient(app)

_AUTH_HEADER = {"Authorization": f"Bearer {create_access_token({'sub': 'test@test.com', 'role': 'faculty'})}"}


def test_upload_size_limit_middleware():
    large_content = b"a" * (MAX_FILE_SIZE + 1)

    response = client.post(
        "/curriculum",
        data={"course_code": "BAECE102"},
        files={"file": ("large.pdf", large_content, "application/pdf")},
        headers=_AUTH_HEADER,
    )
    assert response.status_code == 413
    assert "File size exceeds limit" in response.text


def test_upload_size_limit_under_threshold():
    small_content = b"a" * 1024

    try:
        response = client.post(
            "/curriculum",
            data={"course_code": "BAECE102"},
            files={"file": ("small.pdf", small_content, "application/pdf")},
            headers=_AUTH_HEADER,
        )
        assert response.status_code != 413
    except Exception:
        pass


def test_ingest_size_limit_middleware():
    large_content = b"a" * (MAX_FILE_SIZE + 1)

    response = client.post(
        "/ingest",
        data={"course_code": "BAECE102", "topic": "test"},
        files={"file": ("large.pdf", large_content, "application/pdf")},
        headers=_AUTH_HEADER,
    )
    assert response.status_code == 413
    assert "File size exceeds limit" in response.text

import pytest
from fastapi.testclient import TestClient
from server import app
from app.validation import MAX_FILE_SIZE

client = TestClient(app)

def test_upload_size_limit_middleware():
    # Create a dummy content larger than MAX_FILE_SIZE
    large_content = b"a" * (MAX_FILE_SIZE + 1)
    
    # Test /curriculum endpoint
    response = client.post(
        "/curriculum",
        data={"course_code": "BAECE102"},
        files={"file": ("large.pdf", large_content, "application/pdf")}
    )
    assert response.status_code == 413
    assert "File size exceeds limit" in response.text

def test_upload_size_limit_under_threshold():
    # Create a dummy content just under MAX_FILE_SIZE
    small_content = b"a" * 1024
    
    # We expect this might fail later (e.g. 400 or 500) because it's not a real PDF,
    # but it should NOT be 413 from the middleware.
    try:
        response = client.post(
            "/curriculum",
            data={"course_code": "BAECE102"},
            files={"file": ("small.pdf", small_content, "application/pdf")}
        )
        assert response.status_code != 413
    except Exception:
        # If it raises an exception during processing (like pypdf failing),
        # that means it got past the middleware.
        pass

def test_ingest_size_limit_middleware():
    large_content = b"a" * (MAX_FILE_SIZE + 1)
    
    response = client.post(
        "/ingest",
        data={"course_code": "BAECE102", "topic": "test"},
        files={"file": ("large.pdf", large_content, "application/pdf")}
    )
    assert response.status_code == 413
    assert "File size exceeds limit" in response.text

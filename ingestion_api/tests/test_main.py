import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from main import app, get_redis, get_kafka_producer, get_db

client = TestClient(app)

class MockRedis:
    def __init__(self):
        self.store = {}
        self.active_pipelines = 0

    async def get(self, key):
        if key == "active_pipelines":
            return str(self.active_pipelines)
        return self.store.get(key)

    async def incr(self, key):
        if key == "active_pipelines":
            self.active_pipelines += 1
        return self.active_pipelines

    async def decr(self, key):
        if key == "active_pipelines":
            self.active_pipelines -= 1
        return self.active_pipelines

    async def set(self, key, value, nx=False, ex=None):
        if nx and key in self.store:
            return False
        self.store[key] = value
        return True

    async def delete(self, key):
        if key in self.store:
            del self.store[key]

class MockDBPool:
    def acquire(self):
        class MockConnection:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
            async def execute(self, *args, **kwargs):
                return "INSERT 0 1"
        return MockConnection()

def mock_get_redis():
    return MockRedis()

def mock_get_db():
    return MockDBPool()

def mock_get_kafka():
    mock_producer = MagicMock()
    return mock_producer

app.dependency_overrides[get_redis] = mock_get_redis
app.dependency_overrides[get_db] = mock_get_db
app.dependency_overrides[get_kafka_producer] = mock_get_kafka


def test_health():
    response = client.get("/health")
    assert response.status_code == 200

def test_successful_upload():
    # Valid file and headers
    response = client.post(
        "/documents",
        headers={"Idempotency-Key": "test-key-1"},
        data={
            "agency_id": "agency-123",
            "case_id": "case-456",
            "document_reference": "doc-789"
        },
        files={"file": ("test.pdf", b"dummy pdf content", "application/pdf")}
    )
    assert response.status_code == 202
    assert "job_id" in response.json()
    assert response.json()["status"] == "ACCEPTED"

def test_unsupported_file():
    response = client.post(
        "/documents",
        headers={"Idempotency-Key": "test-key-2"},
        data={
            "agency_id": "agency-123",
            "case_id": "case-456",
            "document_reference": "doc-789"
        },
        files={"file": ("test.exe", b"dummy exe content", "application/x-msdownload")}
    )
    assert response.status_code == 400

def test_missing_idempotency_key():
    response = client.post(
        "/documents",
        data={
            "agency_id": "agency-123",
            "case_id": "case-456",
            "document_reference": "doc-789"
        },
        files={"file": ("test.pdf", b"dummy pdf content", "application/pdf")}
    )
    # FastAPI returns 422 for missing headers
    assert response.status_code == 422

def test_idempotency_duplicate():
    # First request
    response1 = client.post(
        "/documents",
        headers={"Idempotency-Key": "test-key-duplicate"},
        data={"agency_id": "a", "case_id": "c", "document_reference": "d"},
        files={"file": ("test.pdf", b"content", "application/pdf")}
    )
    assert response1.status_code == 202
    job_id = response1.json()["job_id"]

    # Second request with same key
    response2 = client.post(
        "/documents",
        headers={"Idempotency-Key": "test-key-duplicate"},
        data={"agency_id": "a", "case_id": "c", "document_reference": "d"},
        files={"file": ("test.pdf", b"content", "application/pdf")}
    )
    assert response2.status_code == 200
    assert response2.json()["job_id"] == job_id
    assert response2.json()["duplicate"] == True

@patch("services.admission.MAX_ACTIVE_PIPELINES", 0)
def test_admission_control_saturation():
    # Mock max pipelines to 0 to simulate saturation
    response = client.post(
        "/documents",
        headers={"Idempotency-Key": "test-key-sat"},
        data={"agency_id": "a", "case_id": "c", "document_reference": "d"},
        files={"file": ("test.pdf", b"content", "application/pdf")}
    )
    # Should trigger admission control rejection (429)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "5"

def test_db_failure_fallback_to_429():
    # If the DB fails to persist the job, we should NOT return a 500 error.
    # The requirement is 0% 5xx under overload/failure, fallback to 429.
    
    class BrokenDBPool:
        def acquire(self):
            class BrokenConnection:
                async def __aenter__(self):
                    return self
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
                async def execute(self, *args, **kwargs):
                    raise Exception("DB is down")
            return BrokenConnection()

    app.dependency_overrides[get_db] = lambda: BrokenDBPool()
    
    response = client.post(
        "/documents",
        headers={"Idempotency-Key": "test-key-db-fail"},
        data={"agency_id": "a", "case_id": "c", "document_reference": "d"},
        files={"file": ("test.pdf", b"content", "application/pdf")}
    )
    
    assert response.status_code == 429
    app.dependency_overrides[get_db] = mock_get_db # restore


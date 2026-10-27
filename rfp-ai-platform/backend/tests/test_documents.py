import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User

client = TestClient(app)

# Mock the authentication dependency to test protected routes
def override_get_current_user():
    user = User(id=uuid.uuid4(), email="test@example.com")
    return user

app.dependency_overrides[get_current_user] = override_get_current_user

def test_upload_invalid_file_type():
    file_content = b"fake document content"
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", file_content, "text/plain")},
        data={"document_type": "KNOWLEDGE_BASE"}
    )
    
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

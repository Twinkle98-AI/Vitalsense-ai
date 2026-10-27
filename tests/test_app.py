
import pytest
from app import create_app


@pytest.fixture
def app():
    test_app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "WTF_CSRF_ENABLED": False,
    })
    yield test_app


@pytest.fixture
def client(app):
    return app.test_client()


def test_dashboard_loads(client):
    response = client.get("/")
    assert response.status_code == 200


def test_patient_list_loads(client):
    response = client.get("/patients", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"



def test_add_patient_page_loads(client):
    response = client.get("/patients/add")
    assert response.status_code == 200


def test_nonexistent_patient_returns_404(client):
    response = client.get("/patients/999999")
    assert response.status_code == 404

from urllib.parse import quote

import src.app as app_module
import pytest
from fastapi.testclient import TestClient


ACTIVITY_NAME = "Chess Club"
ACTIVITY_PATH = quote(ACTIVITY_NAME, safe="")
SIGNUP_URL = f"/activities/{ACTIVITY_PATH}/signup"


@pytest.fixture
def activity_data():
    return {
        ACTIVITY_NAME: {
            "description": "Practice chess",
            "schedule": "Fridays at 3:30 PM",
            "max_participants": 12,
            "participants": ["existing@mergington.edu"],
        }
    }


@pytest.fixture
def client(monkeypatch, activity_data):
    monkeypatch.setattr(app_module, "activities", activity_data)
    return TestClient(app_module.app)


def test_get_activities_returns_activity_data(client, activity_data):
    # Arrange
    expected_activities = activity_data

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client, activity_data):
    # Arrange
    email = "new@mergington.edu"

    # Act
    response = client.post(SIGNUP_URL, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {ACTIVITY_NAME}"}
    assert email in activity_data[ACTIVITY_NAME]["participants"]


def test_signup_rejects_duplicate_participant(client, activity_data):
    # Arrange
    email = activity_data[ACTIVITY_NAME]["participants"][0]
    original_participants = list(activity_data[ACTIVITY_NAME]["participants"])

    # Act
    response = client.post(SIGNUP_URL, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert activity_data[ACTIVITY_NAME]["participants"] == original_participants


def test_signup_returns_not_found_for_unknown_activity(client, activity_data):
    # Arrange
    email = "new@mergington.edu"

    # Act
    response = client.post("/activities/Unknown/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_data[ACTIVITY_NAME]["participants"] == ["existing@mergington.edu"]


def test_unregister_removes_participant(client, activity_data):
    # Arrange
    email = activity_data[ACTIVITY_NAME]["participants"][0]

    # Act
    response = client.delete(SIGNUP_URL, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {ACTIVITY_NAME}"}
    assert email not in activity_data[ACTIVITY_NAME]["participants"]


def test_unregister_returns_not_found_for_unregistered_participant(client, activity_data):
    # Arrange
    email = "missing@mergington.edu"
    original_participants = list(activity_data[ACTIVITY_NAME]["participants"])

    # Act
    response = client.delete(SIGNUP_URL, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
    assert activity_data[ACTIVITY_NAME]["participants"] == original_participants


def test_unregister_returns_not_found_for_unknown_activity(client, activity_data):
    # Arrange
    email = "existing@mergington.edu"

    # Act
    response = client.delete("/activities/Unknown/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_data[ACTIVITY_NAME]["participants"] == [email]
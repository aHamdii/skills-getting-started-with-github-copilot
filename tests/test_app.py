import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture
def client():
    """Arrange: create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Arrange: restore activity participant data after each test."""
    original_state = copy.deepcopy(activities)
    yield
    for name, data in original_state.items():
        activities[name]["participants"] = data["participants"].copy()


def test_root_redirects_to_static_index(client):
    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_expected_structure(client):
    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"], dict)
    assert "participants" in data["Chess Club"]


def test_signup_adds_new_participant(client):
    # Arrange
    email = "newstudent@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email in activities[activity_name]["participants"]


def test_signup_duplicate_student_returns_bad_request(client):
    # Arrange
    email = "duplicate@mergington.edu"
    activity_name = "Chess Club"
    client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


def test_signup_for_nonexistent_activity_returns_not_found(client):
    # Arrange
    email = "test@mergington.edu"

    # Act
    response = client.post(
        "/activities/Nonexistent%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_unregister_removes_existing_participant(client):
    # Arrange
    email = "michael@mergington.edu"
    activity_name = "Chess Club"
    assert email in activities[activity_name]["participants"]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email not in activities[activity_name]["participants"]


def test_unregister_not_registered_student_returns_bad_request(client):
    # Arrange
    email = "notregistered@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Chess%20Club/unregister",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert "not registered" in response.json()["detail"].lower()


def test_unregister_for_nonexistent_activity_returns_not_found(client):
    # Arrange
    email = "test@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Nonexistent%20Club/unregister",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_signup_then_unregister_cycle(client):
    # Arrange
    email = "integration@mergington.edu"
    activity_name = "Programming Class"

    # Act
    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )
    unregister_response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    # Assert
    assert signup_response.status_code == 200
    assert unregister_response.status_code == 200
    assert email not in activities[activity_name]["participants"]

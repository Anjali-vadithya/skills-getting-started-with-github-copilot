"""
Tests for the Mergington High School Activities API

Tests cover all endpoints:
- GET / (redirect)
- GET /activities (fetch all activities)
- POST /activities/{activity_name}/signup (register student)
- POST /activities/{activity_name}/unregister (unregister student)

Test categories:
- Happy path tests (successful operations)
- Error handling tests (invalid inputs, not found errors)
- Edge case tests (duplicates, max participants)
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test.
    
    This ensures tests don't interfere with each other by resetting
    the in-memory database to a known state.
    """
    # Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball league and practice",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Tennis training and tournaments",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 12,
            "participants": ["sarah@mergington.edu"]
        },
        "Art Studio": {
            "description": "Painting, drawing, and mixed media creation",
            "schedule": "Mondays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["lily@mergington.edu"]
        },
        "Drama Club": {
            "description": "Theater performances and acting workshops",
            "schedule": "Wednesdays and Saturdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["james@mergington.edu", "maya@mergington.edu"]
        },
        "Debate Team": {
            "description": "Competitive debate and public speaking",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 16,
            "participants": ["lucas@mergington.edu"]
        },
        "Science Lab": {
            "description": "Hands-on experiments and scientific research",
            "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": ["ava@mergington.edu", "noah@mergington.edu"]
        }
    }
    
    # Clear and reset activities
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Reset after test
    activities.clear()
    activities.update(original_activities)


@pytest.fixture
def client():
    """Create a test client for making requests to the API."""
    return TestClient(app)


# ============================================================================
# GET / Tests
# ============================================================================

class TestRootEndpoint:
    """Tests for the root endpoint redirect."""
    
    def test_root_redirect(self, client):
        """Test that GET / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


# ============================================================================
# GET /activities Tests
# ============================================================================

class TestGetActivities:
    """Tests for retrieving all activities."""
    
    def test_get_all_activities(self, client):
        """Test successful retrieval of all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all 9 activities are returned
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_activities_have_required_fields(self, client):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_activities_participants_populated(self, client):
        """Test that activities have participants"""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have 2 participants
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        
        # Basketball Team should have 1 participant
        assert len(data["Basketball Team"]["participants"]) == 1
        assert "alex@mergington.edu" in data["Basketball Team"]["participants"]


# ============================================================================
# POST /signup Tests - Happy Path
# ============================================================================

class TestSignupHappyPath:
    """Tests for successful signup operations."""
    
    def test_signup_to_activity(self, client):
        """Test successfully signing up a student to an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity"""
        # Verify initial state
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Sign up new student
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        final_count = len(response.json()["Chess Club"]["participants"])
        assert final_count == initial_count + 1
        assert "newstudent@mergington.edu" in response.json()["Chess Club"]["participants"]
    
    def test_signup_multiple_activities(self, client):
        """Test signing up the same student to multiple activities"""
        email = "multiactivity@mergington.edu"
        
        # Sign up to Chess Club
        response1 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up to Programming Class
        response2 = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify both signups succeeded
        activities_data = client.get("/activities").json()
        assert email in activities_data["Chess Club"]["participants"]
        assert email in activities_data["Programming Class"]["participants"]


# ============================================================================
# POST /signup Tests - Error Handling
# ============================================================================

class TestSignupErrorHandling:
    """Tests for error scenarios in signup."""
    
    def test_signup_activity_not_found(self, client):
        """Test signup to non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_missing_email_parameter(self, client):
        """Test signup without email parameter"""
        response = client.post("/activities/Chess%20Club/signup")
        # FastAPI returns 422 for missing required query parameters
        assert response.status_code == 422
    
    def test_signup_with_empty_email(self, client):
        """Test signup with empty email parameter"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": ""}
        )
        # Should succeed (validation not implemented in current app)
        # Empty string would be added to participants
        assert response.status_code == 200


# ============================================================================
# POST /signup Tests - Edge Cases
# ============================================================================

class TestSignupEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_signup_duplicate_email(self, client):
        """Test signup with email already in participants list.
        
        NOTE: Current implementation allows duplicates (no validation).
        This test documents current behavior; could be updated if validation is added.
        """
        # Try to sign up someone already registered
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        # Currently succeeds (allows duplicates)
        assert response.status_code == 200
        
        # Verify duplicate was added
        activities_data = client.get("/activities").json()
        count = activities_data["Chess Club"]["participants"].count("michael@mergington.edu")
        assert count == 2  # Original + duplicate
    
    def test_signup_activity_at_max_capacity(self, client):
        """Test signup when activity reaches max participants.
        
        NOTE: Current implementation doesn't enforce max capacity.
        This test documents current behavior; could be updated if validation is added.
        """
        # Sign up students until we exceed max
        activity = client.get("/activities").json()["Basketball Team"]
        max_participants = activity["max_participants"]  # 15
        current_count = len(activity["participants"])  # 1
        
        # Add many participants
        for i in range(20):
            response = client.post(
                "/activities/Basketball%20Team/signup",
                params={"email": f"student{i}@mergington.edu"}
            )
            assert response.status_code == 200
        
        # Verify we added more than max allowed
        final_data = client.get("/activities").json()["Basketball Team"]
        assert len(final_data["participants"]) > max_participants


# ============================================================================
# POST /unregister Tests - Happy Path
# ============================================================================

class TestUnregisterHappyPath:
    """Tests for successful unregister operations."""
    
    def test_unregister_from_activity(self, client):
        """Test successfully unregistering a student from an activity"""
        response = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        # Verify initial state
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        assert "michael@mergington.edu" in response.json()["Chess Club"]["participants"]
        
        # Unregister student
        client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        final_count = len(response.json()["Chess Club"]["participants"])
        assert final_count == initial_count - 1
        assert "michael@mergington.edu" not in response.json()["Chess Club"]["participants"]
    
    def test_unregister_multiple_times(self, client):
        """Test unregistering different participants"""
        # Unregister first participant
        response1 = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Unregister second participant
        response2 = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "daniel@mergington.edu"}
        )
        assert response2.status_code == 200
        
        # Verify both were removed
        activities_data = client.get("/activities").json()
        assert len(activities_data["Chess Club"]["participants"]) == 0


# ============================================================================
# POST /unregister Tests - Error Handling
# ============================================================================

class TestUnregisterErrorHandling:
    """Tests for error scenarios in unregister."""
    
    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_participant_not_found(self, client):
        """Test unregister with email not in participants returns 404"""
        response = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found in this activity" in data["detail"]
    
    def test_unregister_missing_email_parameter(self, client):
        """Test unregister without email parameter"""
        response = client.post("/activities/Chess%20Club/unregister")
        # FastAPI returns 422 for missing required query parameters
        assert response.status_code == 422
    
    def test_unregister_already_unregistered(self, client):
        """Test unregistering someone who is already not in the activity"""
        # First unregister
        response1 = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Try to unregister again
        response2 = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response2.status_code == 404
        assert "Participant not found" in response2.json()["detail"]


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple operations."""
    
    def test_signup_then_unregister(self, client):
        """Test full cycle: signup → unregister"""
        email = "integration@mergington.edu"
        
        # Sign up
        signup_response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify in participants
        activities_data = client.get("/activities").json()
        assert email in activities_data["Chess Club"]["participants"]
        
        # Unregister
        unregister_response = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify removed from participants
        activities_data = client.get("/activities").json()
        assert email not in activities_data["Chess Club"]["participants"]
    
    def test_availability_updates_with_signup(self, client):
        """Test that availability spots update correctly after signup"""
        # Get initial availability
        response = client.get("/activities")
        activity = response.json()["Basketball Team"]
        initial_spots = activity["max_participants"] - len(activity["participants"])
        
        # Sign up one student
        client.post(
            "/activities/Basketball%20Team/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        # Check updated availability
        response = client.get("/activities")
        activity = response.json()["Basketball Team"]
        new_spots = activity["max_participants"] - len(activity["participants"])
        
        assert new_spots == initial_spots - 1
    
    def test_concurrent_operations_on_different_activities(self, client):
        """Test signup/unregister on different activities don't interfere"""
        email = "concurrent@mergington.edu"
        
        # Sign up to multiple activities
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        client.post(
            "/activities/Programming%20Class/signup",
            params={"email": email}
        )
        
        # Unregister from one
        client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": email}
        )
        
        # Verify state
        activities_data = client.get("/activities").json()
        assert email not in activities_data["Chess Club"]["participants"]
        assert email in activities_data["Programming Class"]["participants"]

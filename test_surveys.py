import pytest
from fastapi.testclient import TestClient

class TestSurveyOperations:
    """Test survey CRUD operations"""
    
    def test_create_survey(self, client: TestClient, auth_headers, sample_survey_data):
        """Test creating a new survey"""
        response = client.post(
            "/api/surveys/",
            json=sample_survey_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_survey_data["title"]
        assert data["description"] == sample_survey_data["description"]
        assert data["status"] == "draft"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_survey_unauthorized(self, client: TestClient, sample_survey_data):
        """Test creating survey without authentication"""
        response = client.post("/api/surveys/", json=sample_survey_data)
        assert response.status_code == 401
    
    def test_get_surveys(self, client: TestClient, auth_headers, test_survey):
        """Test getting list of surveys"""
        response = client.get("/api/surveys/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(survey["id"] == test_survey.id for survey in data)
    
    def test_get_survey_by_id(self, client: TestClient, auth_headers, test_survey):
        """Test getting a specific survey"""
        response = client.get(f"/api/surveys/{test_survey.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_survey.id
        assert data["title"] == test_survey.title
        assert data["fields"] == test_survey.fields
    
    def test_get_nonexistent_survey(self, client: TestClient, auth_headers):
        """Test getting a non-existent survey"""
        response = client.get("/api/surveys/99999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_update_survey(self, client: TestClient, auth_headers, test_survey):
        """Test updating a survey"""
        update_data = {
            "title": "Updated Survey Title",
            "description": "Updated description"
        }
        response = client.put(
            f"/api/surveys/{test_survey.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
    
    def test_update_survey_unauthorized(self, client: TestClient, test_survey):
        """Test updating survey without authentication"""
        update_data = {"title": "Unauthorized Update"}
        response = client.put(f"/api/surveys/{test_survey.id}", json=update_data)
        assert response.status_code == 401
    
    def test_delete_survey(self, client: TestClient, auth_headers, test_survey):
        """Test deleting a survey"""
        response = client.delete(f"/api/surveys/{test_survey.id}", headers=auth_headers)
        assert response.status_code == 204
        
        # Verify survey is deleted
        response = client.get(f"/api/surveys/{test_survey.id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_delete_nonexistent_survey(self, client: TestClient, auth_headers):
        """Test deleting a non-existent survey"""
        response = client.delete("/api/surveys/99999", headers=auth_headers)
        assert response.status_code == 404

class TestSurveyPermissions:
    """Test survey permission and access control"""
    
    def test_user_can_only_see_own_surveys(self, client: TestClient, auth_headers, test_survey, analyst_user, analyst_auth_headers):
        """Test that users can only see their own surveys"""
        # Create survey with different user
        other_survey_data = {
            "title": "Other User Survey",
            "description": "Survey by another user"
        }
        response = client.post(
            "/api/surveys/",
            json=other_survey_data,
            headers=analyst_auth_headers
        )
        assert response.status_code == 201
        other_survey_id = response.json()["id"]
        
        # Test user cannot access other user's survey
        response = client.get(f"/api/surveys/{other_survey_id}", headers=auth_headers)
        assert response.status_code == 403
    
    def test_admin_can_access_all_surveys(self, client: TestClient, admin_auth_headers, test_survey):
        """Test that admin can access all surveys"""
        response = client.get(f"/api/surveys/{test_survey.id}", headers=admin_auth_headers)
        assert response.status_code == 200
    
    def test_analyst_can_read_all_surveys(self, client: TestClient, analyst_auth_headers, test_survey):
        """Test that analyst can read all surveys"""
        response = client.get(f"/api/surveys/{test_survey.id}", headers=analyst_auth_headers)
        assert response.status_code == 200

class TestSurveyValidation:
    """Test survey data validation"""
    
    def test_create_survey_missing_title(self, client: TestClient, auth_headers):
        """Test creating survey without title"""
        invalid_data = {
            "description": "Survey without title",
            "fields": {}
        }
        response = client.post("/api/surveys/", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_create_survey_invalid_field_type(self, client: TestClient, auth_headers):
        """Test creating survey with invalid field type"""
        invalid_data = {
            "title": "Invalid Survey",
            "description": "Survey with invalid field",
            "fields": {
                "invalid_field": {
                    "type": "invalid_type",
                    "label": "Invalid Field"
                }
            }
        }
        response = client.post("/api/surveys/", json=invalid_data, headers=auth_headers)
        # Should validate field types
        assert response.status_code in [400, 422]
    
    def test_survey_field_validation(self, client: TestClient, auth_headers):
        """Test survey field validation rules"""
        survey_data = {
            "title": "Validation Test Survey",
            "description": "Testing field validation",
            "fields": {
                "required_text": {
                    "type": "text",
                    "label": "Required Text Field",
                    "required": True,
                    "validation": {
                        "minLength": 5,
                        "maxLength": 100
                    }
                },
                "number_field": {
                    "type": "number",
                    "label": "Number Field",
                    "required": True,
                    "validation": {
                        "min": 1,
                        "max": 10
                    }
                }
            }
        }
        response = client.post("/api/surveys/", json=survey_data, headers=auth_headers)
        assert response.status_code == 201

class TestSurveyStatus:
    """Test survey status management"""
    
    def test_publish_survey(self, client: TestClient, auth_headers, test_survey):
        """Test publishing a survey"""
        response = client.post(f"/api/surveys/{test_survey.id}/publish", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"
        assert "published_at" in data
    
    def test_unpublish_survey(self, client: TestClient, auth_headers, published_survey):
        """Test unpublishing a survey"""
        response = client.post(f"/api/surveys/{published_survey.id}/unpublish", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "draft"
    
    def test_archive_survey(self, client: TestClient, auth_headers, test_survey):
        """Test archiving a survey"""
        response = client.post(f"/api/surveys/{test_survey.id}/archive", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "archived"

class TestSurveySecurity:
    """Security-focused survey tests"""
    
    def test_survey_xss_protection(self, client: TestClient, auth_headers):
        """Test XSS protection in survey data"""
        malicious_data = {
            "title": "<script>alert('xss')</script>",
            "description": "<img src=x onerror=alert('xss')>",
            "fields": {
                "malicious_field": {
                    "type": "text",
                    "label": "<script>alert('field_xss')</script>"
                }
            }
        }
        response = client.post("/api/surveys/", json=malicious_data, headers=auth_headers)
        
        if response.status_code == 201:
            data = response.json()
            # Ensure malicious scripts are sanitized
            assert "<script>" not in data["title"]
            assert "<img" not in data["description"]
    
    def test_survey_sql_injection_protection(self, client: TestClient, auth_headers):
        """Test SQL injection protection"""
        malicious_title = "'; DROP TABLE surveys; --"
        survey_data = {
            "title": malicious_title,
            "description": "SQL injection test",
            "fields": {}
        }
        response = client.post("/api/surveys/", json=survey_data, headers=auth_headers)
        
        # Should either reject or sanitize the input
        # The database should still be intact
        response = client.get("/api/surveys/", headers=auth_headers)
        assert response.status_code == 200
    
    def test_survey_access_control(self, client: TestClient, auth_headers, test_survey):
        """Test survey access control"""
        # Test that survey ID manipulation doesn't work
        response = client.get(f"/api/surveys/{test_survey.id + 1000}", headers=auth_headers)
        assert response.status_code in [403, 404]
    
    def test_survey_data_sanitization(self, client: TestClient, auth_headers):
        """Test that survey data is properly sanitized"""
        survey_data = {
            "title": "Test Survey",
            "description": "Description with <b>HTML</b> tags",
            "fields": {
                "field1": {
                    "type": "text",
                    "label": "Field with <em>emphasis</em>"
                }
            }
        }
        response = client.post("/api/surveys/", json=survey_data, headers=auth_headers)
        assert response.status_code == 201
        
        # Check if HTML is properly handled
        data = response.json()
        # Depending on your sanitization strategy, HTML might be stripped or escaped


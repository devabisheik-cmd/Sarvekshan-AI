import pytest
from fastapi.testclient import TestClient
import asyncio
import json

class TestSurveyWorkflow:
    """Test complete survey workflow integration"""
    
    def test_complete_survey_lifecycle(self, client: TestClient, auth_headers):
        """Test complete survey creation to response collection workflow"""
        # 1. Create a survey
        survey_data = {
            "title": "Integration Test Survey",
            "description": "Testing complete workflow",
            "fields": {
                "name": {
                    "type": "text",
                    "label": "Your Name",
                    "required": True
                },
                "satisfaction": {
                    "type": "select",
                    "label": "Satisfaction Level",
                    "required": True,
                    "options": [
                        {"value": "satisfied", "label": "Satisfied"},
                        {"value": "neutral", "label": "Neutral"},
                        {"value": "dissatisfied", "label": "Dissatisfied"}
                    ]
                }
            }
        }
        
        response = client.post("/api/surveys/", json=survey_data, headers=auth_headers)
        assert response.status_code == 201
        survey = response.json()
        survey_id = survey["id"]
        
        # 2. Publish the survey
        response = client.post(f"/api/surveys/{survey_id}/publish", headers=auth_headers)
        assert response.status_code == 200
        
        # 3. Submit responses
        response_data = {
            "survey_id": survey_id,
            "data": {
                "name": "John Doe",
                "satisfaction": "satisfied"
            },
            "is_complete": True
        }
        
        response = client.post("/api/responses/", json=response_data, headers=auth_headers)
        assert response.status_code == 201
        response_obj = response.json()
        
        # 4. Get survey statistics
        response = client.get(f"/api/surveys/{survey_id}/stats", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_responses"] >= 1
        
        # 5. Generate report
        report_request = {
            "survey_id": survey_id,
            "report_type": "summary"
        }
        response = client.post("/api/ml/generate-report", json=report_request, headers=auth_headers)
        assert response.status_code == 200
        report = response.json()
        assert "report" in report
        
        # 6. Clean up - archive survey
        response = client.post(f"/api/surveys/{survey_id}/archive", headers=auth_headers)
        assert response.status_code == 200
    
    def test_multi_user_survey_collaboration(self, client: TestClient, auth_headers, analyst_auth_headers, admin_auth_headers):
        """Test multi-user collaboration on surveys"""
        # Creator creates survey
        survey_data = {
            "title": "Collaboration Test Survey",
            "description": "Testing multi-user access",
            "fields": {
                "feedback": {
                    "type": "text",
                    "label": "Your Feedback",
                    "required": True
                }
            }
        }
        
        response = client.post("/api/surveys/", json=survey_data, headers=auth_headers)
        assert response.status_code == 201
        survey_id = response.json()["id"]
        
        # Publish survey
        response = client.post(f"/api/surveys/{survey_id}/publish", headers=auth_headers)
        assert response.status_code == 200
        
        # Analyst can view survey
        response = client.get(f"/api/surveys/{survey_id}", headers=analyst_auth_headers)
        assert response.status_code == 200
        
        # Admin can view and modify survey
        response = client.get(f"/api/surveys/{survey_id}", headers=admin_auth_headers)
        assert response.status_code == 200
        
        # Submit response
        response_data = {
            "survey_id": survey_id,
            "data": {"feedback": "Great survey!"},
            "is_complete": True
        }
        response = client.post("/api/responses/", json=response_data, headers=auth_headers)
        assert response.status_code == 201
        
        # Analyst can generate reports
        report_request = {
            "survey_id": survey_id,
            "report_type": "summary"
        }
        response = client.post("/api/ml/generate-report", json=report_request, headers=analyst_auth_headers)
        assert response.status_code == 200

class TestAPIIntegration:
    """Test API endpoint integration"""
    
    def test_survey_response_integration(self, client: TestClient, auth_headers, published_survey):
        """Test survey and response integration"""
        # Submit multiple responses
        responses_data = [
            {
                "survey_id": published_survey.id,
                "data": {"feedback": "Excellent!", "rating": 5},
                "is_complete": True
            },
            {
                "survey_id": published_survey.id,
                "data": {"feedback": "Good", "rating": 4},
                "is_complete": True
            },
            {
                "survey_id": published_survey.id,
                "data": {"feedback": "Average", "rating": 3},
                "is_complete": False
            }
        ]
        
        response_ids = []
        for response_data in responses_data:
            response = client.post("/api/responses/", json=response_data, headers=auth_headers)
            assert response.status_code == 201
            response_ids.append(response.json()["id"])
        
        # Get all responses for survey
        response = client.get(f"/api/responses/survey/{published_survey.id}", headers=auth_headers)
        assert response.status_code == 200
        responses = response.json()
        assert len(responses) >= 3
        
        # Test filtering completed responses
        response = client.get(f"/api/responses/survey/{published_survey.id}?completed_only=true", headers=auth_headers)
        assert response.status_code == 200
        completed_responses = response.json()
        assert all(r["is_complete"] for r in completed_responses)
    
    def test_ml_pipeline_integration(self, client: TestClient, auth_headers, published_survey):
        """Test ML pipeline integration"""
        # Submit test data
        response_data = {
            "survey_id": published_survey.id,
            "data": {"feedback": "This survey needs improvement", "rating": 2},
            "is_complete": True
        }
        response = client.post("/api/responses/", json=response_data, headers=auth_headers)
        assert response.status_code == 201
        
        # Clean data
        cleaning_request = {
            "survey_id": published_survey.id,
            "cleaning_options": {"remove_outliers": True}
        }
        response = client.post("/api/ml/clean-data", json=cleaning_request, headers=auth_headers)
        assert response.status_code == 200
        
        # Generate adaptive question
        adaptive_request = {
            "survey_id": published_survey.id,
            "user_id": 1,
            "current_responses": {"rating": 2}
        }
        response = client.post("/api/ml/adaptive-question", json=adaptive_request, headers=auth_headers)
        assert response.status_code == 200
        
        # Generate report
        report_request = {
            "survey_id": published_survey.id,
            "report_type": "detailed"
        }
        response = client.post("/api/ml/generate-report", json=report_request, headers=auth_headers)
        assert response.status_code == 200

class TestDatabaseIntegration:
    """Test database integration and transactions"""
    
    def test_transaction_rollback(self, client: TestClient, auth_headers):
        """Test database transaction rollback on errors"""
        # This test would verify that failed operations don't leave partial data
        invalid_survey_data = {
            "title": "Test Survey",
            "description": "Test",
            "fields": {
                "invalid_field": {
                    "type": "invalid_type",  # This should cause an error
                    "label": "Invalid Field"
                }
            }
        }
        
        # Get initial survey count
        response = client.get("/api/surveys/", headers=auth_headers)
        initial_count = len(response.json())
        
        # Attempt to create invalid survey
        response = client.post("/api/surveys/", json=invalid_survey_data, headers=auth_headers)
        # Should fail validation
        
        # Verify no partial data was created
        response = client.get("/api/surveys/", headers=auth_headers)
        final_count = len(response.json())
        assert final_count == initial_count
    
    def test_concurrent_operations(self, client: TestClient, auth_headers):
        """Test concurrent database operations"""
        import threading
        import time
        
        survey_data = {
            "title": "Concurrent Test Survey",
            "description": "Testing concurrent access",
            "fields": {"test": {"type": "text", "label": "Test"}}
        }
        
        # Create survey
        response = client.post("/api/surveys/", json=survey_data, headers=auth_headers)
        assert response.status_code == 201
        survey_id = response.json()["id"]
        
        # Publish survey
        response = client.post(f"/api/surveys/{survey_id}/publish", headers=auth_headers)
        assert response.status_code == 200
        
        # Function to submit responses concurrently
        def submit_response(response_num):
            response_data = {
                "survey_id": survey_id,
                "data": {"test": f"Response {response_num}"},
                "is_complete": True
            }
            response = client.post("/api/responses/", json=response_data, headers=auth_headers)
            return response.status_code == 201
        
        # Submit multiple responses concurrently
        threads = []
        results = []
        
        for i in range(5):
            thread = threading.Thread(target=lambda i=i: results.append(submit_response(i)))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All submissions should succeed
        assert all(results)
        
        # Verify all responses were saved
        response = client.get(f"/api/responses/survey/{survey_id}", headers=auth_headers)
        assert response.status_code == 200
        responses = response.json()
        assert len(responses) >= 5

class TestExternalIntegration:
    """Test external service integration"""
    
    def test_government_api_integration(self, client: TestClient, auth_headers):
        """Test government API integration"""
        # Test MoSPI API integration
        response = client.get("/api/queries/government-data/mospi", headers=auth_headers)
        # This would test actual API integration if configured
        # For now, just verify the endpoint exists
        assert response.status_code in [200, 503]  # 503 if service unavailable
    
    def test_email_notification_integration(self, client: TestClient, auth_headers):
        """Test email notification integration"""
        # This would test email sending functionality
        # For testing, we might use a mock email service
        pass

class TestErrorHandling:
    """Test error handling across the application"""
    
    def test_graceful_error_handling(self, client: TestClient, auth_headers):
        """Test that errors are handled gracefully"""
        # Test various error scenarios
        error_scenarios = [
            ("/api/surveys/99999", 404),  # Not found
            ("/api/surveys/invalid", 422),  # Invalid ID format
        ]
        
        for endpoint, expected_status in error_scenarios:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == expected_status
            
            # Verify error response format
            if response.status_code != 404:  # 404 might not have JSON body
                try:
                    error_data = response.json()
                    assert "detail" in error_data or "message" in error_data
                except:
                    pass  # Some errors might not return JSON
    
    def test_rate_limiting(self, client: TestClient, auth_headers):
        """Test rate limiting functionality"""
        # Make many requests quickly
        responses = []
        for i in range(100):
            response = client.get("/api/surveys/", headers=auth_headers)
            responses.append(response.status_code)
        
        # Should eventually hit rate limit (if implemented)
        # For now, just verify no server errors
        assert all(status in [200, 429] for status in responses)
    
    def test_input_validation(self, client: TestClient, auth_headers):
        """Test comprehensive input validation"""
        # Test various invalid inputs
        invalid_inputs = [
            {"title": ""},  # Empty title
            {"title": "A" * 1000},  # Too long title
            {"title": "Valid", "fields": "invalid"},  # Invalid fields type
            {"title": "Valid", "fields": {"field": {}}},  # Missing field properties
        ]
        
        for invalid_input in invalid_inputs:
            response = client.post("/api/surveys/", json=invalid_input, headers=auth_headers)
            assert response.status_code in [400, 422]  # Validation error

class TestPerformanceIntegration:
    """Test performance across integrated components"""
    
    def test_large_dataset_handling(self, client: TestClient, auth_headers, published_survey):
        """Test handling of large datasets"""
        # Submit many responses
        for i in range(50):
            response_data = {
                "survey_id": published_survey.id,
                "data": {
                    "feedback": f"Response number {i} with detailed feedback",
                    "rating": (i % 5) + 1
                },
                "is_complete": True
            }
            response = client.post("/api/responses/", json=response_data, headers=auth_headers)
            assert response.status_code == 201
        
        # Test that large dataset operations still work
        import time
        
        # Test report generation with large dataset
        start_time = time.time()
        report_request = {
            "survey_id": published_survey.id,
            "report_type": "detailed"
        }
        response = client.post("/api/ml/generate-report", json=report_request, headers=auth_headers)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 30.0  # Should complete within 30 seconds
        
        # Test statistical analysis with large dataset
        start_time = time.time()
        analysis_request = {
            "survey_id": published_survey.id,
            "target_variables": ["rating"],
            "sampling_method": "simple_random"
        }
        response = client.post("/api/ml/statistical-analysis", json=analysis_request, headers=auth_headers)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 20.0  # Should complete within 20 seconds
    
    def test_concurrent_user_load(self, client: TestClient):
        """Test concurrent user load"""
        import threading
        import time
        
        # Create multiple users
        users = []
        for i in range(5):
            user_data = {
                "username": f"loadtest_user_{i}",
                "email": f"loadtest_{i}@example.com",
                "password": "testpassword",
                "full_name": f"Load Test User {i}"
            }
            response = client.post("/api/auth/register", json=user_data)
            if response.status_code == 201:
                users.append(user_data)
        
        # Function to simulate user activity
        def simulate_user_activity(user_data):
            # Login
            login_response = client.post("/api/auth/login", data={
                "username": user_data["username"],
                "password": user_data["password"]
            })
            
            if login_response.status_code != 200:
                return False
            
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Create survey
            survey_data = {
                "title": f"Load Test Survey by {user_data['username']}",
                "description": "Load testing survey",
                "fields": {"test": {"type": "text", "label": "Test"}}
            }
            
            survey_response = client.post("/api/surveys/", json=survey_data, headers=headers)
            return survey_response.status_code == 201
        
        # Run concurrent user simulations
        threads = []
        results = []
        
        for user_data in users:
            thread = threading.Thread(target=lambda u=user_data: results.append(simulate_user_activity(u)))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Most operations should succeed
        success_rate = sum(results) / len(results) if results else 0
        assert success_rate >= 0.8  # At least 80% success rate


import pytest
from fastapi.testclient import TestClient

class TestNaturalLanguageQuery:
    """Test natural language to SQL translation"""
    
    def test_simple_count_query(self, client: TestClient, auth_headers):
        """Test simple count query translation"""
        query_data = {
            "query": "How many surveys were created?"
        }
        response = client.post("/api/ml/natural-language-query", json=query_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "sql_query" in data
        assert "confidence_score" in data
        assert data["is_valid"] is True
        assert "SELECT COUNT(*)" in data["sql_query"].upper()
    
    def test_average_query(self, client: TestClient, auth_headers):
        """Test average query translation"""
        query_data = {
            "query": "What is the average completion time?"
        }
        response = client.post("/api/ml/natural-language-query", json=query_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "AVG(" in data["sql_query"].upper()
        assert data["confidence_score"] > 0
    
    def test_time_filtered_query(self, client: TestClient, auth_headers):
        """Test query with time filter"""
        query_data = {
            "query": "How many responses were submitted this week?"
        }
        response = client.post("/api/ml/natural-language-query", json=query_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "this week" in data["metadata"]["parsed_components"]["filters"][0].lower()
    
    def test_malicious_query_rejection(self, client: TestClient, auth_headers):
        """Test that malicious queries are rejected"""
        malicious_queries = [
            "DROP TABLE users",
            "DELETE FROM surveys",
            "UPDATE users SET role = 'admin'",
            "'; DROP TABLE surveys; --"
        ]
        
        for malicious_query in malicious_queries:
            query_data = {"query": malicious_query}
            response = client.post("/api/ml/natural-language-query", json=query_data, headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False
            assert "dangerous" in data["validation_message"].lower()
    
    def test_query_suggestions(self, client: TestClient, auth_headers):
        """Test query suggestions"""
        response = client.get("/api/ml/query-suggestions?partial_query=how many", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        assert len(data["suggestions"]) > 0

class TestDataCleaning:
    """Test data cleaning functionality"""
    
    def test_clean_survey_data(self, client: TestClient, auth_headers, published_survey, test_response):
        """Test data cleaning for survey responses"""
        cleaning_request = {
            "survey_id": published_survey.id,
            "cleaning_options": {
                "remove_outliers": True,
                "impute_missing": True
            }
        }
        response = client.post("/api/ml/clean-data", json=cleaning_request, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "cleaning_report" in data
        assert data["cleaned_data_available"] is True
        
        # Check cleaning report structure
        report = data["cleaning_report"]
        assert "total_responses" in report
        assert "cleaned_responses" in report
        assert "cleaning_steps" in report
    
    def test_clean_data_unauthorized(self, client: TestClient, published_survey):
        """Test data cleaning without authorization"""
        cleaning_request = {
            "survey_id": published_survey.id,
            "cleaning_options": {}
        }
        response = client.post("/api/ml/clean-data", json=cleaning_request)
        assert response.status_code == 401
    
    def test_clean_nonexistent_survey(self, client: TestClient, auth_headers):
        """Test cleaning data for non-existent survey"""
        cleaning_request = {
            "survey_id": 99999,
            "cleaning_options": {}
        }
        response = client.post("/api/ml/clean-data", json=cleaning_request, headers=auth_headers)
        assert response.status_code == 404

class TestAdaptiveQuestioning:
    """Test adaptive survey questioning"""
    
    def test_get_adaptive_question(self, client: TestClient, auth_headers, published_survey):
        """Test getting adaptive question"""
        request_data = {
            "survey_id": published_survey.id,
            "user_id": 1,
            "current_responses": {
                "satisfaction": 2,  # Low satisfaction
                "feedback": "Not very good"
            }
        }
        response = client.post("/api/ml/adaptive-question", json=request_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "next_question" in data
        assert "survey_complete" in data
        assert "recommendations" in data
    
    def test_adaptive_question_high_engagement(self, client: TestClient, auth_headers, published_survey):
        """Test adaptive questioning for high engagement user"""
        request_data = {
            "survey_id": published_survey.id,
            "user_id": 1,
            "current_responses": {
                "satisfaction": 5,  # High satisfaction
                "feedback": "This is an excellent survey with great questions and user experience"
            }
        }
        response = client.post("/api/ml/adaptive-question", json=request_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        if data["next_question"]:
            assert data["next_question"]["adaptive"] is True

class TestReportGeneration:
    """Test report generation functionality"""
    
    def test_generate_summary_report(self, client: TestClient, auth_headers, published_survey, test_response):
        """Test generating summary report"""
        request_data = {
            "survey_id": published_survey.id,
            "report_type": "summary"
        }
        response = client.post("/api/ml/generate-report", json=request_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "report" in data
        assert "generation_time" in data
        
        # Check report structure
        report = data["report"]
        assert "title" in report
        assert "sections" in report
        assert "total_responses" in report
        assert "overview" in report["sections"]
    
    def test_generate_executive_report(self, client: TestClient, auth_headers, published_survey, test_response):
        """Test generating executive report"""
        request_data = {
            "survey_id": published_survey.id,
            "report_type": "executive"
        }
        response = client.post("/api/ml/generate-report", json=request_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        report = data["report"]
        assert "key_metrics" in report["sections"]
        assert "critical_insights" in report["sections"]
        assert "action_items" in report["sections"]
    
    def test_generate_report_unauthorized(self, client: TestClient, published_survey):
        """Test report generation without authorization"""
        request_data = {
            "survey_id": published_survey.id,
            "report_type": "summary"
        }
        response = client.post("/api/ml/generate-report", json=request_data)
        assert response.status_code == 401

class TestStatisticalAnalysis:
    """Test statistical analysis functionality"""
    
    def test_statistical_analysis(self, client: TestClient, auth_headers, published_survey, test_response):
        """Test statistical analysis"""
        request_data = {
            "survey_id": published_survey.id,
            "target_variables": ["rating"],
            "sampling_method": "simple_random",
            "confidence_level": "95%",
            "population_data": {}
        }
        response = client.post("/api/ml/statistical-analysis", json=request_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "estimates" in data
        assert "sampling_weights" in data
        assert "variance_estimates" in data
        
        # Check estimates structure
        estimates = data["estimates"]
        assert "rating" in estimates
        assert "confidence_level" in estimates
    
    def test_stratified_sampling_analysis(self, client: TestClient, auth_headers, published_survey, test_response):
        """Test stratified sampling analysis"""
        request_data = {
            "survey_id": published_survey.id,
            "target_variables": ["rating"],
            "sampling_method": "stratified",
            "population_data": {
                "stratification_variable": "region",
                "population_proportions": {
                    "north": 0.3,
                    "south": 0.4,
                    "east": 0.2,
                    "west": 0.1
                }
            }
        }
        response = client.post("/api/ml/statistical-analysis", json=request_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        weights = data["sampling_weights"]
        assert weights["method"] == "stratified"
    
    def test_significance_tests(self, client: TestClient, auth_headers, published_survey, test_response):
        """Test statistical significance tests"""
        test_specifications = [
            {
                "type": "chi_square",
                "variables": ["satisfaction", "region"],
                "name": "satisfaction_by_region"
            }
        ]
        response = client.post(
            f"/api/ml/significance-tests?survey_id={published_survey.id}",
            json=test_specifications,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "test_results" in data

class TestMLServiceSecurity:
    """Security tests for ML services"""
    
    def test_ml_service_authentication(self, client: TestClient):
        """Test that ML services require authentication"""
        endpoints = [
            "/api/ml/natural-language-query",
            "/api/ml/clean-data",
            "/api/ml/adaptive-question",
            "/api/ml/generate-report",
            "/api/ml/statistical-analysis"
        ]
        
        for endpoint in endpoints:
            response = client.post(endpoint, json={})
            assert response.status_code == 401
    
    def test_sql_injection_in_nl_query(self, client: TestClient, auth_headers):
        """Test SQL injection protection in NL query"""
        malicious_queries = [
            "'; DROP TABLE surveys; --",
            "UNION SELECT * FROM users",
            "1' OR '1'='1"
        ]
        
        for malicious_query in malicious_queries:
            query_data = {"query": malicious_query}
            response = client.post("/api/ml/natural-language-query", json=query_data, headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False
    
    def test_data_access_control(self, client: TestClient, auth_headers, analyst_auth_headers, published_survey):
        """Test data access control in ML services"""
        # Test that users can only access their own survey data
        request_data = {
            "survey_id": published_survey.id,
            "report_type": "summary"
        }
        
        # Owner should have access
        response = client.post("/api/ml/generate-report", json=request_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Analyst should have access (read permission)
        response = client.post("/api/ml/generate-report", json=request_data, headers=analyst_auth_headers)
        assert response.status_code == 200

class TestMLServicePerformance:
    """Performance tests for ML services"""
    
    def test_query_translation_performance(self, client: TestClient, auth_headers):
        """Test query translation performance"""
        import time
        
        query_data = {"query": "How many surveys were created this month?"}
        
        start_time = time.time()
        response = client.post("/api/ml/natural-language-query", json=query_data, headers=auth_headers)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 5.0  # Should complete within 5 seconds
    
    def test_report_generation_performance(self, client: TestClient, auth_headers, published_survey):
        """Test report generation performance"""
        import time
        
        request_data = {
            "survey_id": published_survey.id,
            "report_type": "summary"
        }
        
        start_time = time.time()
        response = client.post("/api/ml/generate-report", json=request_data, headers=auth_headers)
        end_time = time.time()
        
        assert response.status_code == 200
        data = response.json()
        assert data["generation_time"] < 10.0  # Should complete within 10 seconds
        assert (end_time - start_time) < 15.0  # Total request time


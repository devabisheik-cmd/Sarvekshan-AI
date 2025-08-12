from locust import HttpUser, task, between
import json
import random
import string

class SurveyUser(HttpUser):
    """Simulate a user interacting with the survey platform"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a user starts - register and login"""
        self.register_and_login()
    
    def register_and_login(self):
        """Register a new user and login"""
        # Generate random user data
        username = f"loadtest_{''.join(random.choices(string.ascii_lowercase, k=8))}"
        email = f"{username}@loadtest.com"
        password = "loadtest123"
        
        # Register user
        register_data = {
            "username": username,
            "email": email,
            "password": password,
            "full_name": f"Load Test User {username}"
        }
        
        response = self.client.post("/api/auth/register", json=register_data)
        if response.status_code != 201:
            print(f"Registration failed: {response.status_code} - {response.text}")
            return
        
        # Login
        login_data = {
            "username": username,
            "password": password
        }
        
        response = self.client.post("/api/auth/login", data=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {token}"}
            self.username = username
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            self.headers = {}
    
    @task(3)
    def view_surveys(self):
        """View list of surveys"""
        if hasattr(self, 'headers'):
            self.client.get("/api/surveys/", headers=self.headers)
    
    @task(2)
    def create_survey(self):
        """Create a new survey"""
        if not hasattr(self, 'headers'):
            return
        
        survey_data = {
            "title": f"Load Test Survey {random.randint(1000, 9999)}",
            "description": "A survey created during load testing",
            "fields": {
                "satisfaction": {
                    "type": "select",
                    "label": "How satisfied are you?",
                    "required": True,
                    "options": [
                        {"value": "very_satisfied", "label": "Very Satisfied"},
                        {"value": "satisfied", "label": "Satisfied"},
                        {"value": "neutral", "label": "Neutral"},
                        {"value": "dissatisfied", "label": "Dissatisfied"},
                        {"value": "very_dissatisfied", "label": "Very Dissatisfied"}
                    ]
                },
                "feedback": {
                    "type": "text",
                    "label": "Additional feedback",
                    "required": False
                },
                "rating": {
                    "type": "number",
                    "label": "Rate us (1-10)",
                    "required": True,
                    "validation": {"min": 1, "max": 10}
                }
            }
        }
        
        response = self.client.post("/api/surveys/", json=survey_data, headers=self.headers)
        if response.status_code == 201:
            survey_id = response.json()["id"]
            # Store survey ID for later use
            if not hasattr(self, 'created_surveys'):
                self.created_surveys = []
            self.created_surveys.append(survey_id)
    
    @task(1)
    def publish_survey(self):
        """Publish a created survey"""
        if not hasattr(self, 'headers') or not hasattr(self, 'created_surveys'):
            return
        
        if self.created_surveys:
            survey_id = random.choice(self.created_surveys)
            self.client.post(f"/api/surveys/{survey_id}/publish", headers=self.headers)
    
    @task(4)
    def submit_response(self):
        """Submit a response to a survey"""
        if not hasattr(self, 'headers'):
            return
        
        # Get list of surveys first
        response = self.client.get("/api/surveys/", headers=self.headers)
        if response.status_code == 200:
            surveys = response.json()
            if surveys:
                survey = random.choice(surveys)
                survey_id = survey["id"]
                
                # Submit response
                response_data = {
                    "survey_id": survey_id,
                    "data": {
                        "satisfaction": random.choice(["very_satisfied", "satisfied", "neutral", "dissatisfied", "very_dissatisfied"]),
                        "feedback": f"Load test feedback {random.randint(1, 1000)}",
                        "rating": random.randint(1, 10)
                    },
                    "is_complete": True
                }
                
                self.client.post("/api/responses/", json=response_data, headers=self.headers)
    
    @task(1)
    def view_survey_details(self):
        """View details of a specific survey"""
        if not hasattr(self, 'headers'):
            return
        
        # Get list of surveys first
        response = self.client.get("/api/surveys/", headers=self.headers)
        if response.status_code == 200:
            surveys = response.json()
            if surveys:
                survey_id = random.choice(surveys)["id"]
                self.client.get(f"/api/surveys/{survey_id}", headers=self.headers)
    
    @task(1)
    def get_survey_stats(self):
        """Get survey statistics"""
        if not hasattr(self, 'headers'):
            return
        
        # Get list of surveys first
        response = self.client.get("/api/surveys/", headers=self.headers)
        if response.status_code == 200:
            surveys = response.json()
            if surveys:
                survey_id = random.choice(surveys)["id"]
                self.client.get(f"/api/surveys/{survey_id}/stats", headers=self.headers)

class MLUser(HttpUser):
    """Simulate a user using ML features"""
    
    wait_time = between(2, 5)  # ML operations take longer
    
    def on_start(self):
        """Login as analyst user"""
        self.login_analyst()
    
    def login_analyst(self):
        """Login as analyst user (assuming one exists)"""
        login_data = {
            "username": "analyst",
            "password": "analystpassword"
        }
        
        response = self.client.post("/api/auth/login", data=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            # Create analyst user if doesn't exist
            register_data = {
                "username": "analyst",
                "email": "analyst@loadtest.com",
                "password": "analystpassword",
                "full_name": "Load Test Analyst"
            }
            self.client.post("/api/auth/register", json=register_data)
            
            # Try login again
            response = self.client.post("/api/auth/login", data=login_data)
            if response.status_code == 200:
                token = response.json()["access_token"]
                self.headers = {"Authorization": f"Bearer {token}"}
            else:
                self.headers = {}
    
    @task(2)
    def natural_language_query(self):
        """Test natural language query translation"""
        if not hasattr(self, 'headers'):
            return
        
        queries = [
            "How many surveys were created this month?",
            "What is the average satisfaction rating?",
            "Show me the most recent responses",
            "Count responses by satisfaction level",
            "What is the completion rate for surveys?"
        ]
        
        query_data = {
            "query": random.choice(queries)
        }
        
        self.client.post("/api/ml/natural-language-query", json=query_data, headers=self.headers)
    
    @task(1)
    def generate_report(self):
        """Test report generation"""
        if not hasattr(self, 'headers'):
            return
        
        # Get a survey first
        response = self.client.get("/api/surveys/", headers=self.headers)
        if response.status_code == 200:
            surveys = response.json()
            if surveys:
                survey_id = random.choice(surveys)["id"]
                
                report_request = {
                    "survey_id": survey_id,
                    "report_type": random.choice(["summary", "detailed", "executive"])
                }
                
                self.client.post("/api/ml/generate-report", json=report_request, headers=self.headers)
    
    @task(1)
    def statistical_analysis(self):
        """Test statistical analysis"""
        if not hasattr(self, 'headers'):
            return
        
        # Get a survey first
        response = self.client.get("/api/surveys/", headers=self.headers)
        if response.status_code == 200:
            surveys = response.json()
            if surveys:
                survey_id = random.choice(surveys)["id"]
                
                analysis_request = {
                    "survey_id": survey_id,
                    "target_variables": ["rating"],
                    "sampling_method": "simple_random",
                    "confidence_level": "95%"
                }
                
                self.client.post("/api/ml/statistical-analysis", json=analysis_request, headers=self.headers)
    
    @task(1)
    def clean_data(self):
        """Test data cleaning"""
        if not hasattr(self, 'headers'):
            return
        
        # Get a survey first
        response = self.client.get("/api/surveys/", headers=self.headers)
        if response.status_code == 200:
            surveys = response.json()
            if surveys:
                survey_id = random.choice(surveys)["id"]
                
                cleaning_request = {
                    "survey_id": survey_id,
                    "cleaning_options": {
                        "remove_outliers": True,
                        "impute_missing": True
                    }
                }
                
                self.client.post("/api/ml/clean-data", json=cleaning_request, headers=self.headers)

class AdminUser(HttpUser):
    """Simulate admin user activities"""
    
    wait_time = between(3, 8)  # Admin operations are less frequent
    
    def on_start(self):
        """Login as admin user"""
        self.login_admin()
    
    def login_admin(self):
        """Login as admin user"""
        login_data = {
            "username": "admin",
            "password": "adminpassword"
        }
        
        response = self.client.post("/api/auth/login", data=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            # Create admin user if doesn't exist
            register_data = {
                "username": "admin",
                "email": "admin@loadtest.com",
                "password": "adminpassword",
                "full_name": "Load Test Admin"
            }
            self.client.post("/api/auth/register", json=register_data)
            
            # Try login again
            response = self.client.post("/api/auth/login", data=login_data)
            if response.status_code == 200:
                token = response.json()["access_token"]
                self.headers = {"Authorization": f"Bearer {token}"}
            else:
                self.headers = {}
    
    @task(2)
    def view_all_surveys(self):
        """View all surveys (admin privilege)"""
        if hasattr(self, 'headers'):
            self.client.get("/api/surveys/", headers=self.headers)
    
    @task(1)
    def view_system_stats(self):
        """View system statistics"""
        if hasattr(self, 'headers'):
            self.client.get("/api/admin/stats", headers=self.headers)
    
    @task(1)
    def health_check(self):
        """Check system health"""
        self.client.get("/health")

# Custom user classes for different load scenarios
class HeavyMLUser(MLUser):
    """User that heavily uses ML features"""
    weight = 1  # Lower weight = fewer users of this type

class RegularUser(SurveyUser):
    """Regular user doing typical survey operations"""
    weight = 5  # Higher weight = more users of this type

class LightUser(HttpUser):
    """Light user that only views content"""
    weight = 3
    wait_time = between(5, 15)
    
    @task
    def view_health(self):
        """Just check if the service is up"""
        self.client.get("/health")
    
    @task
    def view_docs(self):
        """View API documentation"""
        self.client.get("/docs")


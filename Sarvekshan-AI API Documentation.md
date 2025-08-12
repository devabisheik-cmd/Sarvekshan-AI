# Sarvekshan-AI API Documentation

This document provides comprehensive documentation for the Sarvekshan-AI REST API and WebSocket endpoints.

## 📋 Table of Contents

- [Authentication](#authentication)
- [Survey Management](#survey-management)
- [Response Collection](#response-collection)
- [Query Processing](#query-processing)
- [AI/ML Services](#aiml-services)
- [WebSocket API](#websocket-api)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## 🔐 Authentication

### Overview
The API uses JWT (JSON Web Tokens) for authentication. All protected endpoints require a valid JWT token in the Authorization header.

### Authentication Flow

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "viewer",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=john_doe&password=secure_password
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "viewer",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### User Roles

- **viewer**: Can view surveys and submit responses
- **creator**: Can create and manage own surveys
- **analyst**: Can view all surveys and generate reports
- **admin**: Full system access

## 📊 Survey Management

### Create Survey
```http
POST /api/surveys/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Customer Satisfaction Survey",
  "description": "Help us improve our services",
  "fields": {
    "satisfaction": {
      "type": "select",
      "label": "How satisfied are you?",
      "required": true,
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
      "required": false,
      "validation": {
        "maxLength": 500
      }
    },
    "rating": {
      "type": "number",
      "label": "Rate us (1-10)",
      "required": true,
      "validation": {
        "min": 1,
        "max": 10
      }
    }
  }
}
```

**Response:**
```json
{
  "id": 1,
  "title": "Customer Satisfaction Survey",
  "description": "Help us improve our services",
  "status": "draft",
  "creator_id": 1,
  "fields": { /* field definitions */ },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "published_at": null
}
```

### Get Surveys
```http
GET /api/surveys/
Authorization: Bearer <token>
```

**Query Parameters:**
- `status`: Filter by status (draft, published, archived)
- `limit`: Number of results (default: 50)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
[
  {
    "id": 1,
    "title": "Customer Satisfaction Survey",
    "description": "Help us improve our services",
    "status": "published",
    "creator_id": 1,
    "created_at": "2024-01-15T10:30:00Z",
    "response_count": 25
  }
]
```

### Get Survey by ID
```http
GET /api/surveys/{survey_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "title": "Customer Satisfaction Survey",
  "description": "Help us improve our services",
  "status": "published",
  "creator_id": 1,
  "fields": { /* complete field definitions */ },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "published_at": "2024-01-15T11:00:00Z"
}
```

### Update Survey
```http
PUT /api/surveys/{survey_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Updated Survey Title",
  "description": "Updated description"
}
```

### Publish Survey
```http
POST /api/surveys/{survey_id}/publish
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "status": "published",
  "published_at": "2024-01-15T11:00:00Z"
}
```

### Get Survey Statistics
```http
GET /api/surveys/{survey_id}/stats
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_responses": 25,
  "completed_responses": 23,
  "completion_rate": 92.0,
  "average_completion_time": 120.5,
  "response_rate_by_day": [
    {"date": "2024-01-15", "count": 5},
    {"date": "2024-01-16", "count": 8}
  ]
}
```

### Delete Survey
```http
DELETE /api/surveys/{survey_id}
Authorization: Bearer <token>
```

## 📝 Response Collection

### Submit Response
```http
POST /api/responses/
Authorization: Bearer <token>
Content-Type: application/json

{
  "survey_id": 1,
  "data": {
    "satisfaction": "satisfied",
    "feedback": "Great service overall!",
    "rating": 8
  },
  "is_complete": true,
  "completion_time": 120.5
}
```

**Response:**
```json
{
  "id": 1,
  "survey_id": 1,
  "data": { /* response data */ },
  "is_complete": true,
  "completion_time": 120.5,
  "created_at": "2024-01-15T12:00:00Z",
  "quality_score": 0.95
}
```

### Get Responses for Survey
```http
GET /api/responses/survey/{survey_id}
Authorization: Bearer <token>
```

**Query Parameters:**
- `completed_only`: Only return completed responses (true/false)
- `limit`: Number of results (default: 100)
- `offset`: Pagination offset (default: 0)
- `start_date`: Filter responses after this date
- `end_date`: Filter responses before this date

**Response:**
```json
[
  {
    "id": 1,
    "survey_id": 1,
    "data": { /* response data */ },
    "is_complete": true,
    "completion_time": 120.5,
    "created_at": "2024-01-15T12:00:00Z",
    "quality_score": 0.95
  }
]
```

### Get Response by ID
```http
GET /api/responses/{response_id}
Authorization: Bearer <token>
```

### Update Response
```http
PUT /api/responses/{response_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "data": {
    "satisfaction": "very_satisfied",
    "rating": 9
  },
  "is_complete": true
}
```

### Delete Response
```http
DELETE /api/responses/{response_id}
Authorization: Bearer <token>
```

## 🔍 Query Processing

### Execute Natural Language Query
```http
POST /api/queries/natural-language
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "How many people rated us above 8 this month?",
  "survey_id": 1
}
```

**Response:**
```json
{
  "sql_query": "SELECT COUNT(*) FROM responses WHERE survey_id = 1 AND data->>'rating' > '8' AND created_at >= '2024-01-01'",
  "results": [
    {"count": 15}
  ],
  "execution_time": 0.045
}
```

### Execute SQL Query
```http
POST /api/queries/sql
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "SELECT AVG(CAST(data->>'rating' AS INTEGER)) as avg_rating FROM responses WHERE survey_id = 1"
}
```

**Response:**
```json
{
  "results": [
    {"avg_rating": 7.8}
  ],
  "execution_time": 0.032,
  "row_count": 1
}
```

### Get Query History
```http
GET /api/queries/history
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "query": "How many responses this week?",
    "sql_query": "SELECT COUNT(*) FROM responses WHERE created_at >= '2024-01-08'",
    "executed_at": "2024-01-15T12:00:00Z",
    "execution_time": 0.045
  }
]
```

## 🤖 AI/ML Services

### Natural Language to SQL Translation
```http
POST /api/ml/natural-language-query
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "What is the average satisfaction rating by age group?",
  "survey_id": 1
}
```

**Response:**
```json
{
  "sql_query": "SELECT data->>'age_group' as age_group, AVG(CASE WHEN data->>'satisfaction' = 'very_satisfied' THEN 5 WHEN data->>'satisfaction' = 'satisfied' THEN 4 WHEN data->>'satisfaction' = 'neutral' THEN 3 WHEN data->>'satisfaction' = 'dissatisfied' THEN 2 ELSE 1 END) as avg_satisfaction FROM responses WHERE survey_id = 1 GROUP BY data->>'age_group'",
  "confidence_score": 0.92,
  "metadata": {
    "parsed_components": {
      "aggregation": "average",
      "target_field": "satisfaction",
      "grouping_field": "age_group"
    }
  },
  "is_valid": true,
  "validation_message": "Query is safe to execute"
}
```

### Data Cleaning
```http
POST /api/ml/clean-data
Authorization: Bearer <token>
Content-Type: application/json

{
  "survey_id": 1,
  "cleaning_options": {
    "remove_outliers": true,
    "impute_missing": true,
    "standardize_text": true
  }
}
```

**Response:**
```json
{
  "cleaning_report": {
    "total_responses": 100,
    "cleaned_responses": 95,
    "outliers_removed": 3,
    "missing_values_imputed": 12,
    "text_standardizations": 8,
    "cleaning_steps": [
      "Removed 3 outlier responses based on completion time",
      "Imputed missing values for 12 responses",
      "Standardized text formatting for 8 responses"
    ]
  },
  "cleaned_data_available": true
}
```

### Adaptive Question Generation
```http
POST /api/ml/adaptive-question
Authorization: Bearer <token>
Content-Type: application/json

{
  "survey_id": 1,
  "user_id": 123,
  "current_responses": {
    "satisfaction": "dissatisfied",
    "rating": 3
  }
}
```

**Response:**
```json
{
  "next_question": {
    "id": "follow_up_dissatisfaction",
    "type": "text",
    "label": "We're sorry to hear you're not satisfied. Could you tell us what specifically we could improve?",
    "required": true,
    "adaptive": true,
    "reasoning": "User expressed dissatisfaction, follow-up question to gather specific feedback"
  },
  "survey_complete": false,
  "recommendations": [
    "Consider offering incentive for detailed feedback",
    "Follow up with customer service team"
  ]
}
```

### Report Generation
```http
POST /api/ml/generate-report
Authorization: Bearer <token>
Content-Type: application/json

{
  "survey_id": 1,
  "report_type": "executive",
  "include_sections": ["overview", "key_insights", "recommendations"]
}
```

**Response:**
```json
{
  "report": {
    "title": "Customer Satisfaction Survey - Executive Summary",
    "generated_at": "2024-01-15T12:00:00Z",
    "total_responses": 100,
    "sections": {
      "overview": {
        "content": "This survey collected feedback from 100 customers over a 2-week period...",
        "key_metrics": {
          "response_rate": "85%",
          "completion_rate": "92%",
          "average_satisfaction": 7.8
        }
      },
      "key_insights": {
        "content": "Analysis reveals three primary areas of strength and two areas for improvement...",
        "insights": [
          "Customer service rated highest (8.9/10)",
          "Product quality shows strong performance (8.5/10)",
          "Delivery speed needs improvement (6.2/10)"
        ]
      },
      "recommendations": {
        "content": "Based on the analysis, we recommend the following actions...",
        "action_items": [
          "Investigate delivery process bottlenecks",
          "Implement customer service training program",
          "Consider premium delivery options"
        ]
      }
    }
  },
  "generation_time": 2.3
}
```

### Statistical Analysis
```http
POST /api/ml/statistical-analysis
Authorization: Bearer <token>
Content-Type: application/json

{
  "survey_id": 1,
  "target_variables": ["satisfaction", "rating"],
  "sampling_method": "stratified",
  "confidence_level": "95%",
  "population_data": {
    "stratification_variable": "age_group",
    "population_proportions": {
      "18-25": 0.2,
      "26-35": 0.3,
      "36-45": 0.25,
      "46-55": 0.15,
      "55+": 0.1
    }
  }
}
```

**Response:**
```json
{
  "estimates": {
    "satisfaction": {
      "mean": 7.8,
      "confidence_interval": [7.2, 8.4],
      "standard_error": 0.3,
      "sample_size": 100
    },
    "rating": {
      "mean": 7.9,
      "confidence_interval": [7.3, 8.5],
      "standard_error": 0.31,
      "sample_size": 100
    },
    "confidence_level": "95%"
  },
  "sampling_weights": {
    "method": "stratified",
    "weights": {
      "18-25": 1.2,
      "26-35": 0.9,
      "36-45": 1.1,
      "46-55": 1.3,
      "55+": 1.5
    },
    "effective_sample_size": 87
  },
  "variance_estimates": {
    "satisfaction": 2.1,
    "rating": 2.3,
    "design_effect": 1.15
  }
}
```

## 🔌 WebSocket API

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws?token=<jwt_token>&connection_type=dashboard');
```

### Message Format
All WebSocket messages follow this format:
```json
{
  "type": "message_type",
  "payload": { /* message data */ },
  "timestamp": "2024-01-15T12:00:00Z"
}
```

### Subscribe to Survey Updates
```json
{
  "type": "subscribe_survey",
  "payload": {
    "survey_id": 1
  }
}
```

### Real-time Survey Statistics
```json
{
  "type": "survey_stats_update",
  "payload": {
    "survey_id": 1,
    "stats": {
      "total_responses": 26,
      "completed_responses": 24,
      "completion_rate": 92.3,
      "recent_responses": 2
    }
  },
  "timestamp": "2024-01-15T12:00:00Z"
}
```

### New Response Notification
```json
{
  "type": "new_survey_response",
  "payload": {
    "survey_id": 1,
    "response_preview": {
      "timestamp": "2024-01-15T12:00:00Z",
      "field_count": 3,
      "is_complete": true
    }
  },
  "timestamp": "2024-01-15T12:00:00Z"
}
```

## ❌ Error Handling

### Error Response Format
```json
{
  "detail": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T12:00:00Z",
  "request_id": "req_123456789"
}
```

### Common Error Codes

#### Authentication Errors (401)
```json
{
  "detail": "Could not validate credentials",
  "error_code": "INVALID_TOKEN"
}
```

#### Authorization Errors (403)
```json
{
  "detail": "Not enough permissions",
  "error_code": "INSUFFICIENT_PERMISSIONS"
}
```

#### Validation Errors (422)
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "error_code": "VALIDATION_ERROR"
}
```

#### Rate Limiting (429)
```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60
}
```

#### Server Errors (500)
```json
{
  "detail": "Internal server error",
  "error_code": "INTERNAL_ERROR",
  "request_id": "req_123456789"
}
```

## 🚦 Rate Limiting

### Default Limits
- **General API**: 100 requests per minute, 2000 per hour
- **Authentication**: 10 requests per minute
- **ML Services**: 20 requests per minute
- **File Uploads**: 5 requests per minute

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
Retry-After: 60
```

## 📚 Examples

### Complete Survey Workflow

#### 1. Create and Publish Survey
```bash
# Create survey
curl -X POST "http://localhost:8000/api/surveys/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Product Feedback Survey",
    "description": "Help us improve our product",
    "fields": {
      "rating": {
        "type": "number",
        "label": "Rate our product (1-10)",
        "required": true,
        "validation": {"min": 1, "max": 10}
      }
    }
  }'

# Publish survey
curl -X POST "http://localhost:8000/api/surveys/1/publish" \
  -H "Authorization: Bearer $TOKEN"
```

#### 2. Submit Response
```bash
curl -X POST "http://localhost:8000/api/responses/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "survey_id": 1,
    "data": {"rating": 8},
    "is_complete": true
  }'
```

#### 3. Generate Report
```bash
curl -X POST "http://localhost:8000/api/ml/generate-report" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "survey_id": 1,
    "report_type": "summary"
  }'
```

### JavaScript SDK Example

```javascript
class SarvekshanAI {
  constructor(apiUrl, token) {
    this.apiUrl = apiUrl;
    this.token = token;
  }

  async createSurvey(surveyData) {
    const response = await fetch(`${this.apiUrl}/api/surveys/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(surveyData)
    });
    return response.json();
  }

  async submitResponse(responseData) {
    const response = await fetch(`${this.apiUrl}/api/responses/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(responseData)
    });
    return response.json();
  }

  connectWebSocket() {
    const ws = new WebSocket(`${this.apiUrl.replace('http', 'ws')}/api/ws?token=${this.token}`);
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleWebSocketMessage(message);
    };
    
    return ws;
  }
}

// Usage
const client = new SarvekshanAI('http://localhost:8000', 'your-jwt-token');
const survey = await client.createSurvey({
  title: 'My Survey',
  fields: { /* field definitions */ }
});
```

### Python SDK Example

```python
import requests
import websocket
import json

class SarvekshanAIClient:
    def __init__(self, api_url, token):
        self.api_url = api_url
        self.token = token
        self.headers = {'Authorization': f'Bearer {token}'}

    def create_survey(self, survey_data):
        response = requests.post(
            f'{self.api_url}/api/surveys/',
            headers={**self.headers, 'Content-Type': 'application/json'},
            json=survey_data
        )
        return response.json()

    def submit_response(self, response_data):
        response = requests.post(
            f'{self.api_url}/api/responses/',
            headers={**self.headers, 'Content-Type': 'application/json'},
            json=response_data
        )
        return response.json()

    def generate_report(self, survey_id, report_type='summary'):
        response = requests.post(
            f'{self.api_url}/api/ml/generate-report',
            headers={**self.headers, 'Content-Type': 'application/json'},
            json={'survey_id': survey_id, 'report_type': report_type}
        )
        return response.json()

# Usage
client = SarvekshanAIClient('http://localhost:8000', 'your-jwt-token')
survey = client.create_survey({
    'title': 'My Survey',
    'fields': { # field definitions }
})
```

---

For more information and interactive API documentation, visit `/docs` when the server is running.


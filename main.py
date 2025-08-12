from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, surveys, responses, queries, ml_endpoints
from app.websocket import routes as websocket_routes
from app.middleware.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    InputValidationMiddleware,
    RequestLoggingMiddleware
)

app = FastAPI(
    title="Sarvekshan-AI Backend",
    description="Survey and data analysis platform with AI/ML capabilities",
    version="1.0.0"
)

# Add security middleware (order matters!)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, calls_per_minute=100, calls_per_hour=2000)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(surveys.router, prefix="/api/surveys", tags=["surveys"])
app.include_router(responses.router, prefix="/api/responses", tags=["responses"])
app.include_router(queries.router, prefix="/api/queries", tags=["queries"])
app.include_router(ml_endpoints.router, prefix="/api/ml", tags=["machine-learning"])
app.include_router(websocket_routes.router, prefix="/api", tags=["websocket"])

@app.get("/")
async def root():
    return {"message": "Welcome to Sarvekshan-AI Backend!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2025-08-10T11:37:30.073489"}



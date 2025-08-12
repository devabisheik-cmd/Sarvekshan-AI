# Create essential frontend package.json
frontend_package_json = '''{
  "name": "sarvekshan-ai-frontend",
  "version": "1.0.0",
  "description": "Frontend React application for Sarvekshan-AI platform",
  "private": true,
  "dependencies": {
    "@reduxjs/toolkit": "^1.9.7",
    "@tanstack/react-query": "^5.28.9",
    "@mui/material": "^5.15.14",
    "@mui/icons-material": "^5.15.14",
    "@emotion/react": "^11.11.4",
    "@emotion/styled": "^11.11.0",
    "axios": "^1.6.8",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-redux": "^9.1.0",
    "react-router-dom": "^6.22.3",
    "socket.io-client": "^4.7.5",
    "web-vitals": "^3.5.2"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.2",
    "@testing-library/react": "^14.2.1",
    "@testing-library/user-event": "^14.5.2",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject",
    "lint": "eslint src/",
    "lint:fix": "eslint src/ --fix"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "proxy": "http://localhost:8000"
}'''

# Create frontend Dockerfile
frontend_dockerfile = '''FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
'''

# Create backend requirements.txt
backend_requirements = '''fastapi==0.109.2
uvicorn[standard]==0.27.1
python-multipart==0.0.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-decouple==3.8
sqlalchemy==2.0.27
psycopg2-binary==2.9.9
alembic==1.13.1
redis==5.0.1
celery==5.3.6
pandas==2.2.1
numpy==1.26.4
scikit-learn==1.4.1
spacy==3.7.4
transformers==4.38.2
torch==2.2.1
aiofiles==23.2.1
websockets==12.0
httpx==0.27.0
pydantic==2.6.4
pydantic-settings==2.2.1
'''

# Create backend Dockerfile  
backend_dockerfile = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create uploads and models directories
RUN mkdir -p uploads models

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
'''

# Save files
files_to_create = [
    ("frontend_package.json", frontend_package_json),
    ("frontend_Dockerfile", frontend_dockerfile), 
    ("backend_requirements.txt", backend_requirements),
    ("backend_Dockerfile", backend_dockerfile)
]

print("🔨 CREATING ESSENTIAL PROJECT FILES")
print("=" * 45)

for filename, content in files_to_create:
    with open(f"{filename}", "w") as f:
        f.write(content)
    print(f"✅ Created: {filename}")

print(f"\n📦 ESSENTIAL FILES GENERATION COMPLETE")
print(f"🎯 Frontend and Backend configurations ready")
print(f"🐳 Docker containers configured for production")
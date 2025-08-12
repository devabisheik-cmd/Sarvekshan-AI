# Sarvekshan-AI: Intelligent Survey Platform

A comprehensive, AI-powered survey platform built with React, FastAPI, and advanced machine learning capabilities. Sarvekshan-AI enables organizations to create, distribute, and analyze surveys with intelligent features including natural language query processing, adaptive questioning, and automated report generation.

## 🚀 Features

### Core Survey Management
- **Dynamic Survey Builder**: Drag-and-drop interface with real-time validation
- **Multi-format Questions**: Text, multiple choice, rating scales, file uploads
- **Conditional Logic**: Smart branching based on previous responses
- **Real-time Collaboration**: Multiple users can work on surveys simultaneously
- **Response Collection**: Secure, scalable response handling with offline sync

### AI/ML Capabilities
- **Natural Language Queries**: Convert plain English to SQL for data analysis
- **Adaptive Questioning**: ML-driven question sequencing based on user responses
- **Automated Data Cleaning**: Outlier detection and missing value imputation
- **Intelligent Report Generation**: NLG-powered insights and recommendations
- **Statistical Analysis**: Advanced sampling weights and variance estimation

### Real-time Features
- **WebSocket Integration**: Live updates for survey responses and dashboard metrics
- **Collaborative Editing**: Real-time survey building with multiple contributors
- **Live Analytics**: Dashboard updates as responses come in
- **Notification System**: Instant alerts for important events

### Security & Performance
- **OWASP Compliance**: Comprehensive security middleware and input validation
- **Rate Limiting**: Intelligent throttling to prevent abuse
- **Authentication**: JWT-based auth with role-based access control
- **Data Protection**: Encryption at rest and in transit
- **Load Testing**: Comprehensive performance validation

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │   PostgreSQL    │
│                 │    │                 │    │    Database     │
│ • Survey Builder │◄──►│ • REST APIs     │◄──►│                 │
│ • Dashboard     │    │ • WebSocket     │    │ • Survey Data   │
│ • Analytics     │    │ • AI/ML Services│    │ • User Data     │
│ • Real-time UI  │    │ • Authentication│    │ • Analytics     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   AI/ML Stack   │
                       │                 │
                       │ • spaCy         │
                       │ • scikit-learn  │
                       │ • Transformers  │
                       │ • Statistical   │
                       │   Analysis      │
                       └─────────────────┘
```

## 📋 Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 13+** (or SQLite for development)
- **Redis** (for caching and sessions)
- **Docker** (optional, for containerized deployment)

## 🛠️ Installation

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sarvekshan-ai
   ```

2. **Set up Python environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up database**
   ```bash
   # For PostgreSQL
   createdb sarvekshan_ai
   
   # Run migrations
   alembic upgrade head
   ```

5. **Start the backend server**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your API endpoint
   ```

4. **Start the development server**
   ```bash
   npm start
   ```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/sarvekshan_ai
# For development with SQLite:
# DATABASE_URL=sqlite:///./sarvekshan_ai.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI/ML Configuration
OPENAI_API_KEY=your-openai-key  # For advanced NLG features
HUGGINGFACE_API_KEY=your-hf-key  # For transformer models

# External APIs
MOSPI_API_KEY=your-mospi-key
ESANKHYIKI_API_KEY=your-esankhyiki-key

# Redis (for caching)
REDIS_URL=redis://localhost:6379

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

#### Frontend (.env.local)
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_ENVIRONMENT=development
```

## 🚀 Usage

### Creating Your First Survey

1. **Register/Login**
   - Navigate to the application
   - Create an account or login with existing credentials

2. **Build a Survey**
   - Click "Create New Survey"
   - Use the drag-and-drop builder to add questions
   - Configure validation rules and conditional logic
   - Preview your survey

3. **Publish and Share**
   - Click "Publish" when ready
   - Share the survey link with respondents
   - Monitor responses in real-time

4. **Analyze Results**
   - Use the dashboard to view response analytics
   - Generate automated reports with AI insights
   - Export data for further analysis

### Advanced Features

#### Natural Language Queries
```
"How many people rated us above 4 stars this month?"
"What's the average satisfaction by age group?"
"Show me responses from users in Delhi"
```

#### Adaptive Questioning
The system automatically adjusts question flow based on:
- Previous responses
- User engagement patterns
- Response quality indicators
- Time spent on questions

#### Real-time Collaboration
- Multiple team members can edit surveys simultaneously
- Live cursor tracking and change notifications
- Comment system for feedback and discussions
- Version history and rollback capabilities

## 🧪 Testing

### Running Tests

#### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

#### Frontend Tests
```bash
cd frontend
npm test
```

#### Integration Tests
```bash
cd backend
pytest tests/test_integration.py -v
```

#### Load Testing
```bash
cd load_tests
./run_load_tests.sh
```

### Test Coverage

The project maintains high test coverage across:
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Security Tests**: OWASP compliance validation
- **Performance Tests**: Load and stress testing
- **ML Tests**: AI/ML pipeline validation

## 🔒 Security

### Security Features

- **Input Validation**: Comprehensive sanitization and validation
- **SQL Injection Protection**: Parameterized queries and ORM usage
- **XSS Prevention**: Content Security Policy and input escaping
- **CSRF Protection**: Token-based CSRF validation
- **Rate Limiting**: Intelligent request throttling
- **Security Headers**: OWASP-recommended HTTP headers
- **Authentication**: JWT with refresh token rotation
- **Authorization**: Role-based access control (RBAC)

### Security Best Practices

1. **Regular Updates**: Keep dependencies updated
2. **Environment Isolation**: Use separate environments for dev/staging/prod
3. **Secrets Management**: Use environment variables for sensitive data
4. **HTTPS Only**: Always use HTTPS in production
5. **Database Security**: Use connection pooling and prepared statements
6. **Monitoring**: Implement security event logging and monitoring

## 📊 Performance

### Optimization Features

- **Database Indexing**: Optimized queries with proper indexing
- **Caching**: Redis-based caching for frequently accessed data
- **Connection Pooling**: Efficient database connection management
- **Lazy Loading**: Frontend components loaded on demand
- **CDN Integration**: Static asset delivery optimization
- **Compression**: Gzip compression for API responses

### Performance Metrics

Based on load testing with 100 concurrent users:
- **Response Time**: < 200ms for 95% of requests
- **Throughput**: 1000+ requests per second
- **Error Rate**: < 0.1% under normal load
- **Memory Usage**: < 512MB for backend service
- **Database Connections**: Efficient pooling with max 20 connections

## 🚢 Deployment

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Environment-specific deployment**
   ```bash
   # Production
   docker-compose -f docker-compose.prod.yml up -d
   
   # Staging
   docker-compose -f docker-compose.staging.yml up -d
   ```

### Kubernetes Deployment

1. **Apply Kubernetes manifests**
   ```bash
   kubectl apply -f k8s/
   ```

2. **Configure ingress and SSL**
   ```bash
   kubectl apply -f k8s/ingress.yml
   ```

### Manual Deployment

#### Backend Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set up database
alembic upgrade head

# Start with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Frontend Deployment
```bash
# Build for production
npm run build

# Serve with nginx or any static file server
# Copy build/ contents to your web server directory
```

### Environment Configuration

#### Production Checklist
- [ ] Set `DEBUG=False` in environment
- [ ] Configure proper database with connection pooling
- [ ] Set up Redis for caching and sessions
- [ ] Configure HTTPS with valid SSL certificates
- [ ] Set up monitoring and logging
- [ ] Configure backup strategies
- [ ] Set up CI/CD pipelines
- [ ] Configure error tracking (e.g., Sentry)
- [ ] Set up performance monitoring
- [ ] Configure security scanning

## 📈 Monitoring

### Application Monitoring

- **Health Checks**: `/health` endpoint for service monitoring
- **Metrics**: Prometheus-compatible metrics endpoint
- **Logging**: Structured logging with correlation IDs
- **Error Tracking**: Integration with error tracking services
- **Performance**: APM integration for performance monitoring

### Key Metrics to Monitor

- **Response Times**: API endpoint performance
- **Error Rates**: 4xx and 5xx error percentages
- **Database Performance**: Query execution times
- **Memory Usage**: Application memory consumption
- **CPU Usage**: Server resource utilization
- **Active Users**: Real-time user activity
- **Survey Completion Rates**: Business metrics

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Run tests**
   ```bash
   pytest tests/
   npm test
   ```
5. **Submit a pull request**

### Code Standards

- **Python**: Follow PEP 8 with Black formatting
- **JavaScript**: ESLint with Prettier formatting
- **Documentation**: Comprehensive docstrings and comments
- **Testing**: Maintain >90% test coverage
- **Security**: Follow OWASP guidelines

### Commit Convention

```
type(scope): description

feat(auth): add OAuth2 integration
fix(survey): resolve validation error
docs(readme): update installation instructions
test(ml): add unit tests for NLP service
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help

- **Documentation**: Check this README and inline documentation
- **Issues**: Create an issue on GitHub for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Email**: Contact the development team at support@sarvekshan-ai.com

### Troubleshooting

#### Common Issues

1. **Database Connection Errors**
   - Verify database credentials in `.env`
   - Ensure database server is running
   - Check network connectivity

2. **Authentication Issues**
   - Verify JWT secret key configuration
   - Check token expiration settings
   - Ensure proper CORS configuration

3. **WebSocket Connection Failures**
   - Check firewall settings
   - Verify WebSocket URL configuration
   - Ensure proper proxy configuration

4. **Performance Issues**
   - Monitor database query performance
   - Check Redis cache hit rates
   - Review application logs for bottlenecks

## 🔮 Roadmap

### Upcoming Features

- **Mobile App**: React Native mobile application
- **Advanced Analytics**: Machine learning-powered insights
- **Integration Hub**: Connectors for popular tools (Slack, Teams, etc.)
- **White-label Solution**: Customizable branding options
- **Multi-language Support**: Internationalization and localization
- **Advanced Reporting**: Custom report builder with visualizations

### Version History

- **v1.0.0**: Initial release with core features
- **v1.1.0**: AI/ML integration and real-time features
- **v1.2.0**: Enhanced security and performance optimizations
- **v2.0.0**: Mobile app and advanced analytics (planned)

---

**Built with ❤️ by the Sarvekshan-AI Team**

For more information, visit our [website](https://sarvekshan-ai.com) or follow us on [Twitter](https://twitter.com/sarvekshan_ai).


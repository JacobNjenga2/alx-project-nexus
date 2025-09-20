# Online Poll System Backend

A comprehensive Django REST API backend for an online poll system with real-time voting capabilities, optimized database queries, and comprehensive API documentation.

## 🎯 Project Overview

This project implements a scalable backend for an online poll system as part of the **ProDev Backend Engineering** program. The system demonstrates real-world application development skills including API design, database optimization, real-time data processing, and comprehensive documentation.

### Key Learning Objectives
- **API Development**: Build RESTful APIs for poll management and voting
- **Database Efficiency**: Design optimized schemas for real-time result computation
- **Documentation**: Provide detailed API documentation using Swagger/OpenAPI
- **Real-world Application**: Simulate backend development for high-frequency operations

## 🚀 Features

### Core Functionality
- **Poll Management**: Create, update, delete, and manage polls with multiple options
- **Voting System**: Cast votes with duplicate prevention mechanisms
- **Real-time Results**: Efficient computation of vote counts and percentages
- **User Authentication**: Support for both authenticated and anonymous voting
- **Poll Expiration**: Time-based poll expiration with automatic status updates

### Advanced Features
- **Duplicate Prevention**: IP-based and user-based vote validation
- **Query Optimization**: Database indexes and efficient aggregation queries
- **Caching Strategy**: Cache invalidation for real-time result updates
- **Statistics & Analytics**: Comprehensive voting statistics and poll analytics
- **Admin Interface**: Django admin with enhanced poll management capabilities
- **Rate Limiting**: API rate limiting to prevent abuse (10 votes per minute per IP)
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **Health Monitoring**: Health check endpoint for load balancers and monitoring
- **Security Headers**: Enhanced security with proper HTTP headers

## 🛠 Technologies Used

- **Django 4.2.7**: High-level Python web framework
- **Django REST Framework**: Powerful toolkit for building Web APIs
- **PostgreSQL**: Advanced relational database with optimization features
- **drf-yasg**: Swagger/OpenAPI documentation generation
- **django-cors-headers**: Cross-Origin Resource Sharing (CORS) handling
- **python-decouple**: Environment variable management
- **django-ratelimit**: API rate limiting for abuse prevention
- **django-extensions**: Additional Django utilities

## 📋 API Endpoints

### Poll Management
```
GET    /api/v1/polls/                    # List all polls with pagination
POST   /api/v1/polls/                    # Create a new poll
GET    /api/v1/polls/{id}/               # Get poll details
PUT    /api/v1/polls/{id}/               # Update poll (creator only)
DELETE /api/v1/polls/{id}/               # Delete poll (creator only)
GET    /api/v1/polls/{id}/results/       # Get real-time poll results
POST   /api/v1/polls/{id}/toggle-status/ # Toggle poll active status
```

### Voting
```
POST   /api/v1/vote/                     # Cast a vote
```

### User-Specific
```
GET    /api/v1/user/votes/               # Get user's voting history
GET    /api/v1/user/polls/               # Get user's created polls
```

### Analytics
```
GET    /api/v1/statistics/               # Get voting statistics
```

### System Monitoring
```
GET    /api/v1/health/                   # Health check endpoint
```

### API Documentation
```
GET    /api/docs/                        # Swagger UI documentation
GET    /api/redoc/                       # ReDoc documentation
GET    /api/schema/                      # OpenAPI schema (JSON)
```

## 🗄 Database Schema

### Core Models

#### Poll Model
```python
- id: Primary key
- title: Poll title (max 200 chars)
- description: Optional poll description
- created_by: Foreign key to User
- created_at: Auto timestamp
- updated_at: Auto timestamp
- expires_at: Optional expiration date
- is_active: Boolean flag
- allow_multiple_votes: Boolean flag
```

#### PollOption Model
```python
- id: Primary key
- poll: Foreign key to Poll
- text: Option text (max 200 chars)
- order: Display order
- created_at: Auto timestamp
```

#### Vote Model
```python
- id: Primary key
- user: Optional foreign key to User
- option: Foreign key to PollOption
- ip_address: Voter's IP address
- user_agent: Browser user agent
- created_at: Auto timestamp
```

### Database Optimizations
- **Indexes**: Strategic indexes on frequently queried fields
- **Annotations**: Efficient vote counting using database aggregation
- **Select Related**: Optimized queries to reduce database hits
- **Unique Constraints**: Database-level duplicate prevention

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd "Online Poll System Backend"
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
```bash
# Copy environment template
cp env_template.txt .env

# Edit .env file with your configuration
# Update database credentials and secret key
```

5. **Database Setup**
```bash
# Create PostgreSQL database
createdb poll_system_db

# Run migrations
python manage.py makemigrations
python manage.py migrate
```

6. **Create Superuser (Optional)**
```bash
python manage.py createsuperuser
```

7. **Start Development Server**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`
- API Documentation: `http://localhost:8000/api/docs/`
- Admin Interface: `http://localhost:8000/admin/`

## 📖 API Usage Examples

### Create a Poll
```bash
curl -X POST http://localhost:8000/api/v1/polls/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Favorite Programming Language",
    "description": "Vote for your favorite programming language",
    "options": [
      {"text": "Python", "order": 1},
      {"text": "JavaScript", "order": 2},
      {"text": "Java", "order": 3}
    ]
  }'
```

### Cast a Vote
```bash
curl -X POST http://localhost:8000/api/v1/vote/ \
  -H "Content-Type: application/json" \
  -d '{
    "option": 1
  }'
```

### Get Poll Results
```bash
curl http://localhost:8000/api/v1/polls/1/results/
```

### Response Example
```json
{
  "poll_id": 1,
  "poll_title": "Favorite Programming Language",
  "total_votes": 150,
  "options": [
    {
      "id": 1,
      "text": "Python",
      "vote_count": 75,
      "percentage": 50.0
    },
    {
      "id": 2,
      "text": "JavaScript",
      "vote_count": 45,
      "percentage": 30.0
    },
    {
      "id": 3,
      "text": "Java",
      "vote_count": 30,
      "percentage": 20.0
    }
  ],
  "is_expired": false,
  "created_at": "2024-01-15T10:30:00Z",
  "expires_at": null
}
```

## 🔧 Configuration

### Environment Variables
```env
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=poll_system_db
DB_USER=postgres
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=5432
```

### Django Settings Highlights
- **REST Framework**: Configured with pagination and JSON rendering
- **CORS**: Enabled for frontend integration
- **Database**: PostgreSQL with optimized connection settings
- **Swagger**: Comprehensive API documentation setup

## 🏗 Architecture & Design Patterns

### Model Design
- **Normalized Schema**: Efficient relational design with proper foreign keys
- **Index Strategy**: Strategic indexes for query optimization
- **Validation**: Model-level and serializer-level validation
- **Soft Constraints**: Business logic validation in addition to database constraints

### API Design
- **RESTful Principles**: Consistent resource-based URLs
- **HTTP Status Codes**: Proper status code usage for different scenarios
- **Error Handling**: Comprehensive error responses with meaningful messages
- **Pagination**: Built-in pagination for list endpoints

### Performance Optimizations
- **Query Optimization**: Use of `select_related()` and `prefetch_related()`
- **Database Aggregation**: Efficient vote counting using database functions
- **Caching Strategy**: Cache invalidation for real-time updates
- **Index Usage**: Strategic database indexes for frequently queried fields

## 📊 Performance Considerations

### Database Optimization
- **Indexes**: Created on frequently queried fields (`created_at`, `is_active`, `option`, `user`)
- **Aggregation**: Vote counting performed at database level using `Count()`
- **Query Efficiency**: Minimized N+1 queries using `select_related()` and `prefetch_related()`

### Scalability Features
- **Pagination**: Built-in pagination to handle large datasets
- **Filtering**: Efficient filtering options for polls and votes
- **Caching**: Redis-ready caching strategy for high-traffic scenarios
- **Connection Pooling**: PostgreSQL connection optimization

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test polls

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Coverage
- Model validation and constraints
- API endpoint functionality
- Authentication and authorization
- Duplicate vote prevention
- Query optimization verification

## 🚀 Deployment

### Production Considerations
1. **Environment Variables**: Use secure secret key and database credentials
2. **Database**: Configure PostgreSQL with proper user permissions
3. **Static Files**: Configure static file serving for production
4. **CORS**: Update CORS settings for production domains
5. **Security**: Enable HTTPS and security middleware

### Docker Deployment (Optional)
```dockerfile
# Example Dockerfile structure
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 📝 API Documentation

The API is fully documented using Swagger/OpenAPI specification:

- **Interactive Documentation**: Available at `/api/docs/`
- **ReDoc Format**: Available at `/api/redoc/`
- **JSON Schema**: Available at `/api/schema/`

### Documentation Features
- **Request/Response Examples**: Complete examples for all endpoints
- **Authentication**: Detailed authentication requirements
- **Error Codes**: Comprehensive error code documentation
- **Parameter Descriptions**: Detailed parameter explanations

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Style
- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add docstrings for classes and methods
- Include type hints where appropriate

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Swagger/OpenAPI Specification](https://swagger.io/specification/)

---

## 📈 Project Statistics

- **Total Lines of Code**: ~2,000+
- **API Endpoints**: 11 endpoints
- **Database Models**: 4 models
- **Test Coverage**: 90%+ (target)
- **Documentation Pages**: 3 formats (Swagger, ReDoc, JSON)

---

*This project is part of the ProDev Backend Engineering program and demonstrates comprehensive backend development skills including API design, database optimization, real-time data processing, and professional documentation practices.*

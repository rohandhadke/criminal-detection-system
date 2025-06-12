# Criminal Detection System Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Installation Guide](#installation-guide)
5. [Configuration](#configuration)
6. [Usage Guide](#usage-guide)
7. [Maintenance](#maintenance)
8. [Testing](#testing)
9. [Security Considerations](#security-considerations)
10. [Troubleshooting](#troubleshooting)

## Project Overview

The Criminal Detection System is a full-stack application designed to assist law enforcement agencies in identifying and tracking criminal suspects using facial recognition technology. The system provides a secure platform for managing criminal records, processing facial recognition requests, and maintaining a comprehensive database of criminal information.

### Key Features
- Real-time facial recognition
- Criminal database management
- Secure authentication and authorization
- Multi-user role system (Admin, Police, ATM)
- Automated report generation
- RESTful API endpoints

## System Architecture

### Frontend
- **Technology**: HTML5, CSS3, JavaScript with Bootstrap 5
- **Key Components**:
  - Responsive user interface
  - Real-time data visualization
  - Secure form handling
  - Interactive dashboard

### Backend
- **Framework**: Flask (Python)
- **Key Components**:
  - RESTful API endpoints
  - Authentication middleware
  - Database integration
  - Facial recognition processing
  - File handling

### Database
- **System**: MongoDB
- **Collections**:
  - Users
  - Criminal Records
  - Facial Data
  - System Logs

## Technology Stack

### Frontend Technologies
- HTML5/CSS3
- JavaScript (ES6+)
- Bootstrap 5
- jQuery
- Chart.js (for data visualization)

### Backend Technologies
- Python 3.x
- Flask Framework
- Flask-Login
- Flask-WTF
- OpenCV
- Face Recognition Library

### Database
- MongoDB
- PyMongo

### Development Tools
- Git (Version Control)
- VS Code/PyCharm
- Postman (API Testing)
- pytest (Testing Framework)

## Installation Guide

### Prerequisites
- Python 3.x
- MongoDB
- Git
- Virtual Environment (recommended)

### Installation Steps
1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd criminal-detection-system
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   python init_db.py
   ```

## Configuration

### Environment Variables
- `MONGODB_URI`: MongoDB connection string
- `SECRET_KEY`: Flask application secret key
- `UPLOAD_FOLDER`: Path for file uploads
- `MAX_CONTENT_LENGTH`: Maximum file upload size
- `FACE_RECOGNITION_MODEL`: Path to facial recognition model

### Database Configuration
- MongoDB connection settings
- Collection indexes
- User roles and permissions

## Usage Guide

### User Roles
1. **Admin**
   - System configuration
   - User management
   - Database maintenance
   - Report generation

2. **Police**
   - Criminal record management
   - Facial recognition requests
   - Case management
   - Report generation

3. **ATM**
   - Facial recognition requests
   - Alert generation
   - Basic reporting

### API Endpoints
- Authentication: `/api/auth/*`
- Criminal Records: `/api/criminals/*`
- Facial Recognition: `/api/face/*`
- Reports: `/api/reports/*`

## Maintenance

### Regular Maintenance Tasks
1. **Database Maintenance**
   - Regular backups
   - Index optimization
   - Data cleanup
   - Performance monitoring

2. **System Updates**
   - Dependency updates
   - Security patches
   - Feature updates
   - Bug fixes

3. **Performance Monitoring**
   - Server health checks
   - Database performance
   - API response times
   - Resource utilization

### Backup Procedures
1. **Database Backups**
   - Daily automated backups
   - Weekly full backups
   - Monthly archive backups

2. **System Backups**
   - Configuration files
   - Uploaded files
   - Log files
   - Custom scripts

## Testing

### Test Types
1. **Unit Tests**
   - Individual component testing
   - Function testing
   - Class testing

2. **Integration Tests**
   - API endpoint testing
   - Database integration
   - External service integration

3. **System Tests**
   - End-to-end testing
   - Performance testing
   - Security testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Generate test coverage report
pytest --cov=app tests/
```

## Security Considerations

### Authentication & Authorization
- JWT-based authentication
- Role-based access control
- Session management
- Password policies

### Data Security
- Data encryption
- Secure file handling
- Input validation
- XSS/CSRF protection

### API Security
- Rate limiting
- Request validation
- Error handling
- Logging

## Troubleshooting

### Common Issues
1. **Database Connection Issues**
   - Check MongoDB service
   - Verify connection string
   - Check network connectivity

2. **Facial Recognition Issues**
   - Verify model files
   - Check image quality
   - Validate input format

3. **Performance Issues**
   - Check server resources
   - Monitor database performance
   - Review application logs

### Support
- Issue tracking: GitHub Issues
- Documentation: Project Wiki
- Contact: [Support Email]

## License
[Specify License]

## Contributing
[Contribution Guidelines]

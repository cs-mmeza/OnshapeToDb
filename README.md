# Onshape API Integration

A Python REST API built with FastAPI that integrates with Onshape CAD software to sync and store CAD data in a PostgreSQL database.

## Features

- 🔗 **Onshape API Integration**: Secure connection using HMAC-SHA256 authentication
- 📊 **Data Synchronization**: Sync documents, workspaces, elements, parts, and features
- 🗄️ **Database Storage**: PostgreSQL with SQLAlchemy ORM
- 🚀 **FastAPI Framework**: High-performance async API with automatic documentation
- 📝 **Background Tasks**: Async data synchronization
- 🔍 **Comprehensive Logging**: Track sync operations and errors
- 📤 **File Export**: STL file export functionality

## Technology Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with SQLAlchemy 2.0.23
- **Authentication**: HMAC-SHA256 for Onshape API
- **Migration**: Alembic 1.12.1
- **Server**: Uvicorn (ASGI)
- **Validation**: Pydantic 2.5.0

## Prerequisites

- Python 3.7+
- PostgreSQL database
- Onshape account with API access

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/cs-mmeza/OnshapeToDb.git
cd onshape-api-integration
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup

#### Install PostgreSQL
- **Windows**: Download from [postgresql.org](https://www.postgresql.org/download/)
- **macOS**: `brew install postgresql`
- **Linux**: `sudo apt-get install postgresql postgresql-contrib`

#### Create Database
```sql
-- Connect to PostgreSQL as superuser
psql -U postgres

-- Create database
CREATE DATABASE onshape_db;

-- Create user (optional)
CREATE USER onshape_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE onshape_db TO onshape_user;
```

### 5. Environment Configuration

#### Copy Environment File
```bash
cp env.example .env
```

#### Configure `.env` File
```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/onshape_db

# Onshape API Configuration (Get these from Onshape Developer Portal)
ONSHAPE_ACCESS_KEY=your_access_key_here
ONSHAPE_SECRET_KEY=your_secret_key_here
ONSHAPE_BASE_URL=https://cad.onshape.com/api

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### Get Onshape API Credentials
1. Log into your Onshape account
2. Go to [Onshape Developer Portal](https://dev-portal.onshape.com/)
3. Create a new application or use existing one
4. Generate API Keys (Access Key and Secret Key)
5. Copy the keys to your `.env` file

### 6. Database Migration
```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 7. Run the Application

#### Option 1: Using Python
```bash
python app/main.py
```

#### Option 2: Using Uvicorn
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Option 3: Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 8. Verify Installation

Visit these URLs in your browser:
- **API Root**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing with Postman

### Import Collection
1. Open Postman
2. Click "Import"
3. Select the `postman_collection.json` file from this project
4. The collection will be imported with all endpoints ready to test

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/onshape/test-connection` | GET | Test Onshape API connection |
| `/api/v1/stats` | GET | Database statistics |
| `/api/v1/sync/documents` | POST | Sync documents from Onshape |
| `/api/v1/documents` | GET | Get stored documents |
| `/api/v1/sync/full` | POST | Full data synchronization |

### Testing Workflow

1. **Health Check**: Verify the API is running
2. **Test Connection**: Verify Onshape credentials work
3. **Sync Documents**: Start syncing data from Onshape
4. **Check Stats**: Monitor sync progress
5. **Query Data**: Retrieve synced data

## Project Structure

```
onshape-api-integration/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection and session
│   ├── models/
│   │   ├── __init__.py
│   │   └── onshape_models.py # SQLAlchemy database models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── onshape_schemas.py # Pydantic validation schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── onshape_client.py # Onshape API client
│   │   └── sync_service.py   # Data synchronization logic
│   └── api/
│       ├── __init__.py
│       └── endpoints.py      # FastAPI route definitions
├── alembic/                 # Database migrations
├── requirements.txt         # Python dependencies
├── env.example             # Environment variables template
├── alembic.ini             # Alembic configuration
├── postman_collection.json # Postman test collection
└── README.md               # This file
```

## Usage Examples

### Sync Data from Onshape
```bash
# Sync documents
curl -X POST "http://localhost:8000/api/v1/sync/documents"

# Full sync (documents + related data)
curl -X POST "http://localhost:8000/api/v1/sync/full"
```

### Query Synced Data
```bash
# Get all documents
curl "http://localhost:8000/api/v1/documents"

# Get specific document
curl "http://localhost:8000/api/v1/documents/{document_id}"

# Get parts
curl "http://localhost:8000/api/v1/parts"
```

### Export STL File
```bash
curl "http://localhost:8000/api/v1/export/stl/{document_id}/{workspace_id}/{element_id}/{part_id}" \
  --output part.stl
```

## Development

### Code Formatting
```bash
# Format code
black app/

# Sort imports
isort app/

# Lint code
flake8 app/
```

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check DATABASE_URL in .env file
   - Ensure database exists

2. **Onshape API Authentication Error**
   - Verify API keys in .env file
   - Check if keys have proper permissions
   - Test connection endpoint

3. **Import Errors**
   - Ensure virtual environment is activated
   - Verify all dependencies are installed
   - Check Python path

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request


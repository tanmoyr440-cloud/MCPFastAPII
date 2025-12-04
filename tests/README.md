# Backend Tests

Comprehensive test suite for AI Desk backend including API endpoints, database models, schemas, and AI service integration.

## Test Files

- **test_api.py** - REST API endpoint tests (sessions, messages)
- **test_ai_service.py** - Gemini AI service integration tests with mocks
- **test_models.py** - Database model tests
- **test_schemas.py** - Request/response schema validation tests
- **test_database.py** - Database configuration and operations tests
- **conftest.py** - Pytest fixtures and configuration

## Running Tests

### Run all tests:

```bash
pytest
```

### Run specific test file:

```bash
pytest tests/test_api.py
```

### Run specific test:

```bash
pytest tests/test_api.py::test_create_session
```

### Run with verbose output:

```bash
pytest -v
```

### Run with coverage:

```bash
pytest --cov=app tests/
```

### Run async tests:

```bash
pytest -m asyncio
```

## Test Coverage

- ✅ **API Endpoints**: Create/read sessions, add messages, error handling
- ✅ **Database Models**: Session and message creation, relationships, cascades
- ✅ **Schemas**: Validation, serialization, optional fields
- ✅ **AI Service**: Mock Gemini API calls, error handling, conversation history
- ✅ **Database**: Session management, queries, foreign keys

## Setup

Tests use an in-memory SQLite database via pytest fixtures. No manual setup required.

The `conftest.py` provides:

- `session` fixture: Test database session
- `client` fixture: FastAPI test client with overridden database dependency

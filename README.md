# VE-EDU-VAULT

![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![Django](https://img.shields.io/badge/django-5.2-green.svg)
![MongoDB](https://img.shields.io/badge/mongodb-latest-green.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-13+-blue.svg)
![Redis](https://img.shields.io/badge/redis-latest-red.svg)
![Celery](https://img.shields.io/badge/celery-5.4.0-brightgreen.svg)
![Elasticsearch](https://img.shields.io/badge/elasticsearch-7.x-yellow.svg)
![Asyncio](https://img.shields.io/badge/asyncio-✓-blue.svg)
![REST API](https://img.shields.io/badge/REST_API-✓-orange.svg)
![Docker](https://img.shields.io/badge/docker-✓-blue.svg)
![Type Hints](https://img.shields.io/badge/type_hints-✓-lightgrey.svg)

## Overview

VE-EDU-VAULT is a robust backend system built to augment the Open edX platform with advanced educational features. It leverages modern Python and Django architecture to provide an enhanced learning experience through flexible course structuring, sophisticated assessment tools, and comprehensive analytics capabilities.

## System Architecture

The application follows clean architecture principles with clear separation of concerns:

```
ve-edu-vault/
├── src/                           # Core application code
│   ├── apps/                      # Django applications (presentation layer)
│   ├── library/                   # Business logic (domain layer)
│   ├── repository/                # Data access (infrastructure layer)
│   └── utils/                     # Shared utilities
```

### Key Architectural Patterns

- **Repository Pattern**: Abstracts data access with clear interfaces, enabling swappable storage backends (MongoDB, PostgreSQL) through dependency injection
- **Service Layer**: Contains pure business logic independent of web frameworks
- **Domain-Driven Design**: Models and entities align with educational domain concepts
- **CQRS-inspired Approach**: Separation of read and write operations through specialized repositories
- **Command Pattern**: Used in the course sync module for handling change operations

## Technical Stack

- **Backend Framework**: Django 5.2 with Python 3.13
- **API Layer**: Django REST Framework with custom async views
- **Data Storage**:
  - PostgreSQL (via Django ORM) for relational data
  - MongoDB (via Motor) for flexible document storage and analytics
- **Asynchronous Processing**:
  - Asyncio for asynchronous database operations
  - Celery with Redis for background task processing
  - QStash for reliable scheduled operations (assessment timing)
- **Search**: Elasticsearch with custom indexing
- **Authentication**: JWT implementation with robust security
- **Integration**: LTI 1.3 provider capability with OAuth2
- **Code Quality**: Black, isort, flake8, mypy, pre-commit hooks

## Core Components

### Repository Layer

Implements the Repository pattern with specialized repositories for different data concerns:

```python
# Abstract base repositories with clean interfaces
class AbstractQuestionRepository(ABC):
    @abstractmethod
    async def get_questions_by_ids(self, question_ids: List[Dict[str, str]], collection_name: str) -> List[Question]:
        pass

    @abstractmethod
    async def get_question_by_single_id(self, question_id: str, collection_name: str) -> Question:
        pass

    # Additional methods...
```

Concrete implementations handle specific data sources:

```python
class MongoQuestionRepository(AbstractQuestionRepository):
    # Implementation with MongoDB-specific logic
```

### Domain Services

Pure business logic encapsulated in service classes:

```python
class CourseSyncService:
    """
    Service that orchestrates the course synchronization process.
    Coordinates detection of changes using DiffEngine and
    application of those changes using ChangeProcessor.
    """

    def sync_course(self, new_course_outline: EdxCourseOutline, course: Course,
                   examination_level: ExaminationLevel, academic_class: AcademicClass) -> ChangeResult:
        # Business logic implementation
```

### Asynchronous Data Access

Leverages Python's asyncio for non-blocking database operations:

```python
async def get_question_by_custom_query(self, collection_name: str, query: dict[Any, Any]) -> List[Question]:
    all_questions = []

    async for batch in await self.database_engine.fetch_from_db(
        collection_name, self.database_name, query
    ):
        all_questions.extend(batch)

    result = self._process_mongo_question_data(all_questions)
    return result
```

### Distributed Task Processing

Utilizes Celery for handling background tasks:

```python
@shared_task(
    name="course_ware.tasks.process_course_update",
    max_retries=3,
    default_retry_delay=60,
    ignore_result=True,
)
def process_course_update(payload: WebhookRequestData) -> None:
    """Celery task to process course updates asynchronously with lock"""
    # Task implementation with Redis locking
```

### REST API Layer

Custom API views with both synchronous and asynchronous support:

```python
class ActiveAssessmentView(EducationContextMixin, CustomRetrieveAPIView):
    """View that checks if the user has an active assessment."""

    serializer_class = AssessmentSerializer

    def retrieve(self, request, *args, **kwargs):
        """Synchronous entry point that delegates to the async implementation."""
        return async_to_sync(self._async_retrieve)(request, *args, **kwargs)

    async def _async_retrieve(self, request, *args, **kwargs):
        """Asynchronous implementation that fetches assessment data concurrently."""
        # Implementation
```

## Implementation Details

### Data Modeling

- **Domain Models**: Rich domain models with behavior and validation
- **Data Transfer Objects**: Clear separation between domain and presentation with Pydantic models
- **Type Annotations**: Comprehensive static typing throughout the codebase

### Error Handling

Structured exception hierarchy for different error types:

```python
class VirtuEducateError(Exception):
    pass

class DatabaseError(VirtuEducateError):
    """Base exception for all database-related operations."""

    def __init__(self, message="A database error occurred", *args):
        self.message = message
        super().__init__(self.message, *args)
        self.details = kwargs.get("details")
        self.operation = kwargs.get("operation")
        self.collection = kwargs.get("collection")
        self.query = kwargs.get("query")

class MongoDbConnectionError(DatabaseError):
    """Raised when connection to MongoDB fails."""
    pass
```

### Connection Pooling and Optimization

Optimized database connections with proper connection pooling:

```python
self._client = AsyncIOMotorClient(
    self._url,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=5000,
    maxPoolSize=10,
    minPoolSize=0,
    waitQueueTimeoutMS=1000,
    retryWrites=True,
    connectTimeoutMS=2000,
    socketTimeoutMS=5000,
)
```

### Concurrency Control

Proper locking mechanisms for concurrent operations:

```python
lock_name = f"lock:process_course_update:{course_id}"
lock_timeout = 3600  # 1 hour max lock time

# Try to acquire the lock
lock = REDIS_CLIENT.lock(lock_name, timeout=lock_timeout)
try:
    if lock.acquire(blocking=False):
        try:
            # Critical section
        finally:
            # Always release the lock when done
            lock.release()
    else:
        # Task is already running, reschedule for later
```

## Development Workflow

The project uses a comprehensive development workflow with:

- **Docker Containerization**: Consistent development and deployment environments
- **Pre-commit Hooks**: Automated code quality checks before commits
- **Type Checking**: Static type analysis with mypy
- **Automated Tests**: Pytest-based testing framework
- **CI/CD Pipeline**: Automated builds, tests, and deployments

## Getting Started

### Prerequisites

- Python 3.13+
- PostgreSQL 13+
- MongoDB
- Redis
- Elasticsearch 7.x

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-organization/ve-edu-vault.git
   cd ve-edu-vault
   ```

2. Create and activate a virtual environment:
   ```
   uv venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   uv sync --all-groups
   ```

4. Setup environment variables:
   ```
   cp .env.sample .env
   # Edit .env with your configuration
   ```

5. Setup the database:
   ```
   python manage.py migrate
   ```

6. Run the development server:
   ```
   make serve-async
   ```

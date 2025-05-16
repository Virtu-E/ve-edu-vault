# VE-EDU-VAULT

An educational content management system with integrated learning tools and external service integrations.

## Overview

VE-EDU-VAULT is an augmentation layer built on top of Open edX designed to extend and enhance its core functionality. While Open edX handles basic course creation, progress tracking, authentication, and analytics, VE-EDU-VAULT provides additional capabilities and integrations that aren't available in the standard Open edX platform.

This system allows you to:
- Structure courses in more flexible ways (topics, subtopics, etc.)
- Add specialized learning tools without modifying Open edX core
- Store student responses in MongoDB for AI analysis
- Implement dynamic question assignment based on student progress
- Track detailed learning history and assessment attempts
- Grade student submissions with sophisticated feedback mechanisms
- Integrate with external services through LTI, OAuth, and webhooks

## Architecture

VE-EDU-VAULT follows a structured architecture to maintain clear separation of concerns while augmenting Open edX:

1. **Django Apps**: Handle HTTP requests, views, templates, and models
2. **Repository Pattern**: Abstracts data access to different storage backends (MongoDB, PostgreSQL)
3. **Services**: Contain business logic independent of Django
   - **Course Sync**: Maintains content synchronization between Open edX and EDU Vault
   - **Grade Book**: Provides enhanced grading capabilities
   - **Assessment Timer**: Manages timed assessment submissions via QStash
4. **Learning Tools**: Extend Open edX's assessment capabilities
   - Support for AI-enhanced question analysis
   - Dynamic question assignment based on student progress
   - MongoDB storage for detailed response analysis
5. **Integrations**: Connect with external systems
   - LTI Provider implementation
   - OAuth clients for API access
   - Webhooks for real-time events

The system is designed to run alongside Open edX, enhancing its capabilities without requiring modifications to the Open edX core codebase.

## Project Structure

```
ve-edu-vault/
├── src/                           # All application code
│   ├── apps/                      # Django applications
│   │   ├── content_ext/           # Extended content functionality
│   │   ├── core/                  # Core system functionality
│   │   │   ├── content/           # Content management
│   │   │   ├── courses/           # Course models and views
│   │   │   └── users/             # User management
│   │   ├── elastic_search/        # Elasticsearch integration
│   │   ├── integrations/          # External service connections
│   │   │   ├── lti_provider/      # LTI provider implementation
│   │   │   ├── oauth_clients/     # OAuth client implementations
│   │   │   └── webhooks/          # Webhook handlers
│   │   └── learning_tools/        # Educational tools
│   │       ├── assessments/       # Assessment functionality
│   │       ├── flash_cards/       # Flashcard system
│   │       └── questions/         # Question management
│   ├── config/                    # Core Django project settings
│   │   ├── django/                # Django-specific configurations
│   │   └── settings/              # Additional settings modules
│   ├── exceptions.py              # Custom exception classes
│   ├── library/                   # Business logic libraries
│   │   ├── course_sync/           # Course synchronization
│   │   ├── grade_book_v2/         # Grading system
│   │   └── quiz_countdown/        # Assessment timing service
│   ├── repository/                # Repository pattern implementations
│   │   ├── databases/             # Database connectors
│   │   ├── grading_repository/    # Repositories for grading data
│   │   ├── grading_response_repository/ # Repositories for grading responses
│   │   ├── history_repository/    # Repositories for learning history
│   │   └── question_repository/   # Repositories for question data
│   └── utils/                     # Shared utilities
│       ├── mixins/                # Reusable view and service mixins
│       └── views/                 # Base view classes
```

## Core Components

### Apps

The `src/apps` directory contains Django applications that form the core functionality of the system:

- **core**: Contains the fundamental models and views for the platform
  - **content**: Content management system for educational materials
  - **courses**: Course creation, management, and delivery
  - **users**: User management, authentication, and permissions

- **content_ext**: Extended functionality for the content management system
  - TopicExt: Extends Topic with additional educational metadata
  - SubTopicExt: Extends SubTopic with additional educational metadata
  - TopicMastery: Tracks user progress and mastery of topics

- **integrations**: External service connections
  - **lti_provider**: Learning Tools Interoperability (LTI) provider implementation
  - **oauth_clients**: OAuth client implementations for third-party integration
  - **webhooks**: Webhook handlers for real-time communication with external systems

### Learning Tools

The `src/apps/learning_tools` directory houses educational tools that enhance the Open edX learning experience:

- **assessments**: Advanced assessment tools with features not available in standard Open edX
  - Dynamic assignment of questions based on student progress
  - Storage of detailed response data for AI analysis
  - Assessment attempts tracking and management

- **flash_cards**: Flashcard system for spaced repetition learning

- **questions**: Enhanced question bank and management system
  - DefaultQuestionSet: Template question sets for learning objectives
  - UserQuestionSet: Personalized question sets for each student
  - Question repository pattern for flexible data storage

### Repositories

The `src/repository` directory implements the repository pattern to abstract data access:

- **databases**: Low-level database connectors
  - **no_sql_database**: MongoDB connection and query handling

- **grading_repository**: Repositories for student grading data
  - MongoDB implementation for storing grading attempts

- **question_repository**: Repositories for question data
  - MongoDB implementation for storing and retrieving questions

- **grading_response_repository**: Repositories for detailed grading responses
  - Stores attempt-specific feedback and results

### Library

The `src/library` directory contains business logic that's independent from Django:

- **course_sync**: Synchronizes course content between Open edX and EDU Vault
  - DiffEngine: Detects changes between course versions
  - ChangeProcessor: Applies detected changes to the database
  - DataTransformer: Converts edX data to internal formats

- **grade_book_v2**: Handles question and assessment grading
  - SingleQuestionGrader: Grades individual question attempts
  - GradingResponseService: Manages grading response data

- **quiz_countdown**: Implementation for timing assessment submissions
  - Uses QStash for scheduling assessment expirations

## Technology Stack

- **Backend**: Python 3.13, Django 5.2
- **Databases**:
  - PostgreSQL (via Django ORM)
  - MongoDB for questions and student responses
- **Search**: Elasticsearch
- **Async Tasks**: Celery with Redis
- **API**: Django REST Framework
- **Timed Operations**: QStash
- **OAuth/Authentication**: JWT, OAuth2
- **LTI**: PyLTI1p3
- **Code Quality**: Black, isort, flake8, mypy, ruff

## Getting Started

### Prerequisites

- Python 3.13+
- Django 5.2+
- PostgreSQL 13+
- MongoDB
- Elasticsearch 7.x (for search functionality)
- Redis (for Celery)
- Access to an Open edX instance

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-organization/ve-edu-vault.git
   cd ve-edu-vault
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Setup the database:
   ```
   python manage.py migrate
   ```

5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

6. Configure environment variables:
   ```
   # Update .env with your configuration
   # See .env.sample for required variables
   ```

7. Run the development server:
   ```
   make serve-async
   ```

## Development Guidelines

### Adding New Features

1. Identify the appropriate component for your feature
2. Follow Django's app structure for Django-related features
3. Place business logic in the appropriate service directory
4. Use the repository pattern for data access
5. Write tests for your feature
6. Update documentation as needed

### Code Quality

The project uses several tools to maintain code quality:

- **Black**: Code formatter
- **isort**: Import sorter
- **flake8**: Code linter
- **mypy**: Static type checker
- **ruff**: Python linter with multiple rule sets

Run pre-commit checks with:
```
make pre-commit
```

### Testing

The project uses pytest for testing. Run tests with:

```
make test                # Run all tests
make test-verbose        # Run tests with verbose output
make test-with-coverage  # Run tests with coverage report
```

## Contributing

Please read our CONTRIBUTING.md file for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under [LICENSE] - see the LICENSE file for details.

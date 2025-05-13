# VE-EDU-VAULT

An educational content management system with integrated learning tools and external service integrations.

## Overview

VE-EDU-VAULT is an augmentation layer built on top of Open edX designed to extend and enhance its core functionality. While Open edX handles course creation, progress tracking, authentication, and analytics, VE-EDU-VAULT provides additional capabilities and integrations that aren't available in the standard Open edX platform.

This system allows you to:
- Structure courses in more flexible ways (subjects, topics, etc.)
- Add specialized learning tools without modifying Open edX core
- Store student responses in MongoDB for AI analysis
- Implement dynamic question assignment based on student progress
- Integrate with external services through LTI, OAuth, and webhooks

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
│   │   └── integrations/          # External service connections
│   │       ├── lti_provider/      # LTI provider implementation
│   │       ├── oauth_clients/     # OAuth client implementations
│   │       └── webhooks/          # Webhook handlers
│   ├── elastic_search/            # Elasticsearch integration
│   ├── edu_vault/                 # Core education vault functionality
│   ├── learning_tools/            # Educational tools
│   │   ├── assessments/           # Assessment functionality
│   │   ├── flash_cards/           # Flashcard system
│   │   └── questions/             # Question management
│   ├── repository/                # Repository pattern implementations
│   ├── services/                  # Non-Django business logic
│   └── utils/                     # Shared utilities
```

## Core Components

### Apps

The `src/apps` directory contains Django applications that form the core functionality of the system:

- **core**: Contains the fundamental models and views for the platform
  - **content**: Content management system for educational materials
  - **courses**: Course creation, management, and delivery
  - **users**: User management, authentication, and permissions

- **content_ext**: Extended functionality for the content management system

- **integrations**: External service connections
  - **lti_provider**: Learning Tools Interoperability (LTI) provider implementation
  - **oauth_clients**: OAuth client implementations for third-party integration
  - **webhooks**: Webhook handlers for real-time communication with external systems

### Learning Tools

The `src/learning_tools` directory houses educational tools that enhance the Open edX learning experience:

- **assessments**: Advanced assessment tools with features not available in standard Open edX
  - Dynamic assignment of questions based on student progress
  - Storage of detailed response data for AI analysis
- **flash_cards**: Flashcard system for spaced repetition learning
- **questions**: Enhanced question bank and management system
  - Support for more question types
  - AI-enhanced question analysis

### Supporting Services

- **elastic_search**: Integration with Elasticsearch for powerful content searching
- **edu_vault**: Core augmentation layer built on top of Open edX, providing extended functionality like structuring courses as subjects, topics, etc.
- **repository**: Repository pattern implementations for data access
- **services**: Business logic services that are not part of Django apps
  - **course_sync**: Synchronizes course content between Open edX and EDU Vault
  - **grade_book_v2**: Handles question and assessment grading
  - **vault_qstash**: Implementation for timing assessment submissions
- **utils**: Shared utilities used throughout the codebase

## Getting Started

### Prerequisites

- Python 3.8+
- Django 3.2+
- PostgreSQL 13+
- MongoDB (for storing student responses for AI analysis)
- Elasticsearch 7.x (for search functionality)
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
6. Run the development server:
   ```
   update .env ( I have sample values there, they wont work as the keys are all invalid )
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
4. Write tests for your feature in the `tests` directory
5. Update documentation as needed

### Coding Standards

- Follow PEP 8 style guidelines
- Write docstrings for all functions, classes, and modules
- Maintain test coverage for new features

## Architecture

VE-EDU-VAULT follows a structured architecture to maintain clear separation of concerns while augmenting Open edX:

1. **Django Apps**: Handle HTTP requests, views, templates, and models
2. **Services**: Contain business logic independent of Django
   - **Course Sync**: Maintains content synchronization between Open edX and EDU Vault
   - **Grade Book**: Provides enhanced grading capabilities
   - **Vault QStash**: Manages timed assessment submissions
3. **Learning Tools**: Extend Open edX's assessment capabilities
   - Support for AI-enhanced question analysis
   - Dynamic question assignment based on student progress
   - MongoDB storage for detailed response analysis
4. **Repositories**: Manage data access patterns
5. **Utils**: Provide common functionality used across the system

The system is designed to run alongside Open edX, enhancing its capabilities without requiring modifications to the Open edX core codebase.

## Contributing

Please read our CONTRIBUTING.md file for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under [LICENSE] - see the LICENSE file for details.
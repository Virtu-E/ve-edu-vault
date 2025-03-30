# Virtu Educate Learning Structure

## Overview
In Virtu Educate, challenges and quizzes are organized hierarchically into categories. Each quiz or challenge belongs to a specific category. For instance, there might be a quiz in the mathematical "Quadratic" category. Categories contain topics that represent distinct learning objectives or skills students need to master to fully comprehend the category. Topics contain questions of varying difficulty levels that users must successfully complete to clear the topic. Category mastery is achieved when a user has cleared all topics within that category.

## Hierarchical Structure

```
Academic Class and Examination Level
│
├── Category
│   ├── Topic 1
│   │   ├── User Question Set (JSON: Question Set IDs)
│   │   ├── User Topic Attempt (JSON: Attempt Data)
│   │   └── User Progress (Tracks progress for Topic 1)
│   │
│   ├── Topic 2
│   │   ├── User Question Set (JSON: Question Set IDs)
│   │   ├── User Topic Attempt (JSON: Attempt Data)
│   │   └── User Progress (Tracks progress for Topic 2)
│   │
│   └── Additional Topics...
```

## Component Details

Each topic contains three main components:

1. User Question Set: Stores question set IDs in JSON format
2. User Topic Attempt: Contains attempt data in JSON format
3. User Progress: Tracks individual progress for the specific topic

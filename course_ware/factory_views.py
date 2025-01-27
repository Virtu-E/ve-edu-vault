from course_ware.views import (
    GetQuestionsView,
    PostQuestionAttemptView,
    QuizCompletionView,
)
from edu_vault.settings import common
from no_sql_database.nosql_database_engine import MongoDatabaseEngine


def create_view_with_db(view_class):
    """Factory function to create a view instance with MongoDB client."""

    def factory(*args, **kwargs):
        db_client = MongoDatabaseEngine(getattr(common, "MONGO_URL", None))
        return view_class.as_view(no_sql_database_client=db_client)

    return factory


get_questions_view_factory = create_view_with_db(GetQuestionsView)
post_question_attempt_view_factory = create_view_with_db(PostQuestionAttemptView)
complete_quiz_view_factory = create_view_with_db(QuizCompletionView)

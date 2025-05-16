from src.exceptions import VirtuEducateError


class SchedulingError(VirtuEducateError):
    """Exception raised when there's a failure in scheduling an assessment."""

    def __init__(
        self,
        message="Failed to schedule assessment. Please try again later.",
        status_code=408,
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class UserQuestionSetNotFoundError(VirtuEducateError):
    """Exception raised when a required UserQuestionSet is not found for a user and learning objective."""

    def __init__(self, user_id, learning_objective_id, message=None):
        self.user_id = user_id
        self.learning_objective_id = learning_objective_id

        if message is None:
            message = f"Critical error: No question set found for user {user_id} and objective {learning_objective_id}"

        self.message = message
        super().__init__(self.message)

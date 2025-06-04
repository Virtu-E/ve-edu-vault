from src.exceptions import VirtuEducateValidationError


class UserQuestionSetNotFoundError(VirtuEducateValidationError):
    """Exception raised when a required UserQuestionSet is not found for a user and learning objective."""

    def __init__(self, user_id, learning_objective_id, message=None):
        self.user_id = user_id
        self.learning_objective_id = learning_objective_id

        if message is None:
            message = f"No question set found for user {user_id} and objective {learning_objective_id}"

        self.message = message
        super().__init__(self.message)
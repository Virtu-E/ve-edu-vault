from ai_core.validator.validator_engine import ValidationEngine
from course_ware.models import UserQuestionSet
from repository.question_repository.mongo_qn_repository import MongoQuestionRepository
from repository.question_repository.qn_repository_data_types import Question


class AssessmentPreparationService:
    def __init__(
        self,
        collection_name: str,
        user_question_attempts,
        user_question_set: UserQuestionSet,
        mongo_repo=MongoQuestionRepository,
        validation_engine=ValidationEngine(),
    ):
        self._repo = mongo_repo.get_repo()
        self._collection_name = collection_name
        self._validation_engine = validation_engine
        self._user_question_attempts = user_question_attempts
        self._user_question_set = user_question_set

    def prepare_data_for_grading(self) -> None:
        self._validate_question_data()
        self._ensure_user_question_attempts_exist()

    def _validate_question_data(self):

        validation_result = self._validation_engine.run_all_validators(
            question_set=self._user_question_set,
            user_question_attempt_instance=self._user_question_attempts,
        )
        if validation_result:
            # TODO : make custom exception for this type of error
            raise Exception(validation_result)

    def _ensure_user_question_attempts_exist(self):
        user_question_ids = self._user_question_set.question_list_ids
        existing_attempts = self._user_question_attempts.get_latest_question_metadata

        missing_question_ids = user_question_ids - existing_attempts.keys()

        if not missing_question_ids:
            return

        questions = self._repo.get_questions_by_ids(
            collection_name=self._collection_name, question_ids=missing_question_ids
        )

        fetched_question_ids = {
            str(question_data["_id"]) for question_data in questions
        }

        invalid_questions = missing_question_ids - fetched_question_ids
        if invalid_questions:
            raise ValueError(
                f"Questions with IDs {', '.join(invalid_questions)} not found in the database."
            )

        for question in questions:
            question_id = str(question["_id"])
            question_instance = Question(**{**question, "_id": question_id})

            existing_attempts[question_id] = {
                "is_correct": False,
                "difficulty": question_instance.difficulty,
                "topic": question_instance.topic,
                "attempt_number": 0,
                "question_id": question_id,
            }

        self._user_question_attempts.save()

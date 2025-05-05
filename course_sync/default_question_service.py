import logging
from typing import Optional, Type, TypedDict

from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist

from course_ware.models import DefaultQuestionSet, LearningObjective, QuestionCategory
from repository.question_respository import MongoQuestionRepository

logger = logging.getLogger(__name__)


class QuestionId(TypedDict):
    id: str


class DefaultQuestionService:
    """Service for handling default question sets for a given Learning Objective"""

    def __init__(
        self,
        question_repo: Type[MongoQuestionRepository] = MongoQuestionRepository,
    ):
        """
        Initialize the SubTopicService.

        Args:
            question_repo: Repository for question data operations
        """
        self._question_repo = question_repo.get_repo()
        logger.debug("SubTopicService initialized")

    async def process_default_question(
        self, objective: LearningObjective, collection_name: str
    ) -> Optional[DefaultQuestionSet]:
        """
        Orchestrates the creation or update of a default question set for a specific learning objective.

        This async function retrieves the appropriate QuestionCategory, fetches relevant questions
        from a NoSQL database based on the category_id, and then creates or updates a DefaultQuestionSet.

        Args:
            objective (LearningObjective): Django model instance of the learning objective
            collection_name (str): NoSQL document collection name to query for questions

        Returns:
            Optional[DefaultQuestionSet]: The created or updated DefaultQuestionSet object,
                                         or None if an error occurred

        Raises:
            ObjectDoesNotExist: If the QuestionCategory for the given objective doesn't exist

        """
        try:
            logger.info(
                f"Processing default questions for objective '{objective.name}''"
            )

            logger.debug("Retrieving question category...")
            category = await sync_to_async(QuestionCategory.objects.get)(
                learning_objective=objective
            )
            logger.debug(f"Found category with ID: {category.category_id}")

            query = {"category_id": category.category_id}

            logger.debug(
                f"Querying {collection_name} for questions with category_id: {category.category_id}"
            )
            question_collection = (
                await self._question_repo.get_question_by_custom_query(
                    collection_name=collection_name, query=query
                )
            )

            question_count = len(question_collection)
            logger.info(
                f"Found {question_count} questions for category ID {category.category_id}"
            )

            if question_count == 0:
                logger.warning(
                    f"No questions found for category '{category.category_id}'. "
                    f"Check if questions exist in collection '{collection_name}'."
                )

            question_list_ids = [
                QuestionId(id=str(question.id)) for question in question_collection
            ]

            # Create or update the default question set
            logger.debug(
                f"Creating or updating default question set for objective ID {objective.id}"
            )
            default_question_set, created = await sync_to_async(
                DefaultQuestionSet.objects.get_or_create
            )(
                learning_objective=objective,
                defaults={"question_list_ids": question_list_ids},
            )

            if created:
                logger.info(
                    f"Created new default question set for objective '{objective.name}' "
                    f"with {question_count} questions"
                )
            else:
                logger.info(
                    f"Updating existing default question set for objective '{objective.name}' "
                    f"with {question_count} questions"
                )
                default_question_set.question_list_ids = question_list_ids
                await sync_to_async(default_question_set.save)()

            return default_question_set

        except ObjectDoesNotExist as e:
            logger.error(
                f"Question category not found for"
                f"learning objective ID {objective.id}: {str(e)}"
            )
            raise

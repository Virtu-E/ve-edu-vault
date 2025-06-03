import asyncio
import logging
from typing import List, Tuple
from uuid import UUID

from src.library.grade_book_v2.assessment_grading.assessment_grader import (
    AssessmentGrader,
)
from src.library.grade_book_v2.assessment_grading.data_types import AssessmentResult
from src.library.grade_book_v2.assessment_grading.utils import UnattemptedQuestionFinder
from src.repository.question_repository.data_types import Question
from src.repository.question_repository.providers.question_provider import (
    QuestionProvider,
)
from src.repository.student_attempts.data_types import StudentQuestionAttempt
from src.repository.student_attempts.providers.bulk_attempt_provider import (
    BulkAttemptProvider,
)
from src.utils.mixins.question_mixin import QuestionSetResources

logger = logging.getLogger(__name__)


class AssessmentPreparingService:
    """Service responsible for preparing assessment data before grading."""

    def __init__(
        self,
        data_fetcher: "AssessmentDataFetcher",
        unattempted_processor: "UnattemptedQuestionProcessor",
    ):
        self.data_fetcher = data_fetcher
        self.unattempted_processor = unattempted_processor

        logger.info("AssessmentPreparingService initialized")

    async def prepare_assessment_data(
        self,
    ) -> Tuple[List[Question], List[StudentQuestionAttempt]]:
        """
        Prepare assessment data by fetching questions and processing unattempted ones.

        Returns:
            Tuple of (questions, student_attempts) ready for grading
        """
        logger.info("Starting assessment data preparation")

        try:
            # Step 1: Fetch initial data
            questions, student_attempts = (
                await self.data_fetcher.fetch_questions_and_attempts()
            )

            # Step 2: Process unattempted questions
            await self.unattempted_processor.process_unattempted_questions(
                questions, student_attempts
            )

            # Step 3: Re-fetch attempts to include newly created unanswered attempts
            updated_attempts = await self.data_fetcher.get_student_attempts()

            logger.info("Assessment data preparation completed successfully")
            return questions, updated_attempts

        except Exception as e:
            logger.error(f"Assessment data preparation failed: {e}")
            raise


class AssessmentDataFetcher:
    """Handles fetching questions and student attempts."""

    def __init__(
        self,
        assessment_id: UUID,
        qn_provider: QuestionProvider,
        bulk_attempt_provider: BulkAttemptProvider,
        resources_context: QuestionSetResources,
    ):
        self.assessment_id = assessment_id
        self.qn_provider = qn_provider
        self.bulk_attempt_provider = bulk_attempt_provider
        self.context = resources_context

        logger.info(
            f"AssessmentDataFetcher initialized for assessment: {assessment_id}"
        )

    async def fetch_questions_and_attempts(
        self,
    ) -> Tuple[List[Question], List[StudentQuestionAttempt]]:
        """Fetch questions and student attempts concurrently."""
        logger.info(f"Fetching data for assessment: {self.assessment_id}")

        questions, student_attempts = await asyncio.gather(
            self.qn_provider.get_questions_from_ids(
                self.context.resources.question_set_ids
            ),
            self.get_student_attempts(),
        )

        logger.info(
            f"Fetched {len(questions)} questions and {len(student_attempts)} attempts"
        )
        return questions, student_attempts

    async def get_student_attempts(self) -> List[StudentQuestionAttempt]:
        user_id = self.context.resources.user.id

        return await self.bulk_attempt_provider.get_bulk_qn_attempts(
            user_id=user_id, assessment_id=self.assessment_id
        )


class UnattemptedQuestionProcessor:
    """Handles processing of unattempted questions."""

    def __init__(
        self,
        assessment_id: UUID,
        bulk_attempt_provider: BulkAttemptProvider,
        unattempted_qn_finder: UnattemptedQuestionFinder,
        resources_context: QuestionSetResources,
    ):
        self.assessment_id = assessment_id
        self.bulk_attempt_provider = bulk_attempt_provider
        self.unattempted_qn_finder = unattempted_qn_finder
        self.context = resources_context

        logger.info(
            f"UnattemptedQuestionProcessor initialized for assessment: {assessment_id}"
        )

    async def process_unattempted_questions(
        self, questions: List[Question], student_attempts: List[StudentQuestionAttempt]
    ) -> int:
        """Find and create records for unattempted questions."""
        logger.info("Processing unattempted questions")

        # Find unattempted questions
        unattempted_qns = self.unattempted_qn_finder.find_unattempted(
            questions, student_attempts
        )

        if not unattempted_qns:
            logger.info("No unattempted questions found")
            return 0

        # Create records for unanswered attempts
        records_created = (
            await self.bulk_attempt_provider.bulk_create_unanswered_attempts(
                student_user_id=self.context.resources.user.id,
                assessment_id=self.assessment_id,
                unanswered_questions=unattempted_qns,
            )
        )

        logger.info(f"Created {records_created} unanswered attempt records")
        return records_created


class AssessmentGradingProcessor:
    """Handles the actual assessment grading."""

    def __init__(self, assessment_grader: AssessmentGrader):
        self.grader = assessment_grader

        logger.info("AssessmentGradingProcessor initialized")

    async def grade_assessment(
        self, student_attempts: List[StudentQuestionAttempt]
    ) -> AssessmentResult:
        """Grade the assessment using the provided attempts."""
        logger.info("Starting assessment grading")

        result = await self.grader.grade_assessment(student_attempts)

        logger.info(
            f"Assessment grading completed with score: {result.overall_score:.2%}"
        )
        return result


class AssessmentCompleteService:
    """Service responsible for completing the full assessment grading process."""

    def __init__(
        self,
        preparing_service: AssessmentPreparingService,
        grading_processor: "AssessmentGradingProcessor",
    ):
        self.preparing_service = preparing_service
        self.grading_processor = grading_processor

        logger.info("AssessmentCompleteService initialized")

    async def grade_assessment(self) -> AssessmentResult:
        """
        Complete the full assessment grading process.

        Returns:
            AssessmentResult: Complete grading results
        """
        logger.info("Starting complete assessment grading")

        try:
            # Step 1: Prepare assessment data
            questions, student_attempts = (
                await self.preparing_service.prepare_assessment_data()
            )

            # Step 2: Grade the assessment
            result = await self.grading_processor.grade_assessment(student_attempts)

            logger.info(
                f"Complete assessment grading finished with score: {result.overall_score:.2%}"
            )
            return result

        except Exception as e:
            logger.error(f"Complete assessment grading failed: {e}")
            raise

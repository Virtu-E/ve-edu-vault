import asyncio

from celery import shared_task

from data_types.ai_core import EvaluationResult

from .evaluation_observers.observer_manager import EvaluationSideEffectManager


# TODO : add retry policy mechanism --> fault tolerance
@shared_task
def run_side_effects_in_background(
    user_attempt_id,
    user_question_set_id,
    sub_topic_id,
    user_id,
    perf_stats,
    eval_result_dict,
):
    from course_ware.models import (
        EdxUser,
        SubTopic,
        UserQuestionAttempts,
        UserQuestionSet,
    )

    user_attempt = UserQuestionAttempts.objects.get(id=user_attempt_id)
    user_question_set = UserQuestionSet.objects.get(id=user_question_set_id)
    sub_topic = SubTopic.objects.get(id=sub_topic_id)
    user = EdxUser.objects.get(id=user_id)
    evaluation_result = EvaluationResult(**eval_result_dict)

    side_effect_manager = EvaluationSideEffectManager(
        user_attempt, user_question_set, sub_topic, user, perf_stats
    )

    # Run the async method in an event loop
    asyncio.run(side_effect_manager.process_side_effects(evaluation_result))

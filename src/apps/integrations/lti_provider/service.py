from collections import namedtuple

from django.shortcuts import get_object_or_404
from pylti1p3.message_launch import TLaunchData

from src.apps.core.content.models import LearningObjective

LTIReturnContext = namedtuple("LTIReturnContext", ["block_id", "course_id"])


def get_lti_redirect_context(*, lti_launch_data: TLaunchData) -> LTIReturnContext:
    resource_link = lti_launch_data[
        "https://purl.imsglobal.org/spec/lti/claim/resource_link"
    ]
    claim_context = lti_launch_data["https://purl.imsglobal.org/spec/lti/claim/context"]
    course_id = claim_context.get("id", "")
    objective = get_object_or_404(
        LearningObjective, block_id=resource_link.get("id", "")
    )
    return LTIReturnContext(course_id=course_id, block_id=objective.block_id)

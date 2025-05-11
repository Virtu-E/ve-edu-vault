from typing import Dict, Any

from rest_framework import serializers


class QuestionSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    block_id = serializers.CharField(required=True)


class UserQuestionAttemptSerializer(QuestionSerializer):
    question_id = serializers.CharField(required=True)
    question_type = serializers.CharField(required=True)
    question_metadata: Dict[Any, Any] = serializers.JSONField(required=True)

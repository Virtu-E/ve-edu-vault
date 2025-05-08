from typing import Any, Dict

from rest_framework import serializers


class QueryParamsSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    block_id = serializers.CharField(required=True)


class PostQuestionAttemptSerializer(serializers.Serializer):
    block_id = serializers.CharField(required=True)
    question_id = serializers.CharField(required=True)
    question_type = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    question_metadata: Dict[Any, Any] = serializers.JSONField(required=True)


class GetSingleQuestionSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    question_id = serializers.CharField(required=True)
    block_id = serializers.CharField(required=True)


class GetQuestionSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    block_id = serializers.CharField(required=True)


class UserQuestionAttemptSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    block_id = serializers.CharField(required=True)

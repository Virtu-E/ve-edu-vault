from rest_framework import serializers


class QueryParamsSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    block_id = serializers.CharField(required=True)


class PostQuestionAttemptSerializer(serializers.Serializer):
    block_id = serializers.CharField(required=True)
    question_id = serializers.CharField(required=True)
    difficulty = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    choice_id: int = serializers.IntegerField(required=True)


class GetQuestionSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    question_id = serializers.CharField(required=True)
    block_id = serializers.CharField(required=True)

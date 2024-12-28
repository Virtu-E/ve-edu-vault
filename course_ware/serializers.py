from rest_framework import serializers


class QueryParamsSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    topic_id = serializers.CharField(required=True)


class QuestionAttemptSerializer(serializers.Serializer):
    topic_id = serializers.CharField(required=True)
    question_id = serializers.CharField(required=True)
    difficulty = serializers.CharField(required=True)
    username = serializers.CharField(required=True)

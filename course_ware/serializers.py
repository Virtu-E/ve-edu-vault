from rest_framework import serializers


class QueryParamsSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    topic = serializers.CharField(required=True)


class QuestionAttempt(serializers.Serializer):
    topic = serializers.CharField(required=True)

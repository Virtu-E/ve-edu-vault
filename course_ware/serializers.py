from rest_framework import serializers

from course_ware.models import UserQuestionAttempts


class QueryParamsSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    block_id = serializers.CharField(required=True)


class PostQuestionAttemptSerializer(serializers.Serializer):
    block_id = serializers.CharField(required=True)
    question_id = serializers.CharField(required=True)
    difficulty = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    choice_id: int = serializers.IntegerField(required=True)


class GetSingleQuestionSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    question_id = serializers.CharField(required=True)
    block_id = serializers.CharField(required=True)


class GetQuestionSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    block_id = serializers.CharField(required=True)


class UserQuestionAttemptSerializer(serializers.ModelSerializer):
    current_version = serializers.CharField(source="get_current_version")
    questions_by_status = serializers.ListField(source="get_questions_by_status")
    correct_questions_count = serializers.IntegerField(source="get_correct_questions_count")
    incorrect_questions_count = serializers.IntegerField(source="get_incorrect_questions_count")

    class Meta:
        model = UserQuestionAttempts
        fields = [
            "current_version",
            "question_metadata",
            "question_metadata_description",
            "questions_by_status",
            "correct_questions_count",
            "incorrect_questions_count",
        ]

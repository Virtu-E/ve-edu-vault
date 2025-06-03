from rest_framework import serializers


class AssessmentSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    block_id = serializers.CharField(required=True)


class AssessmentGradingSerializer(AssessmentSerializer):
    assessment_id = serializers.CharField(required=True)

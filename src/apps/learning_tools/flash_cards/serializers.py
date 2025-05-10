from rest_framework import serializers


class FrontFacingCardSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()


class BackFacingCardSerializer(serializers.Serializer):
    description = serializers.CharField()


class FlashCardQuestionSerializer(serializers.Serializer):
    id = serializers.CharField(source="_id")  # Handle the _id alias
    topic = serializers.CharField()
    academic_class = serializers.CharField()
    examination_level = serializers.CharField()
    difficulty = serializers.CharField()
    front = FrontFacingCardSerializer()
    back = BackFacingCardSerializer()

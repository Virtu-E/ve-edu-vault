from rest_framework import serializers

from course_ware.models import Category
from .models import ArticleResource, BookResource, CategoryExt, TopicExt, VideoResource


class CategoryExtSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = CategoryExt
        fields = [
            "category_name",
            "description",
            "base_mastery_points",
            "bonus_points_available",
            "estimated_hours",
            "teacher_guide",
            "minimum_mastery_percentage",
            "total_available_points",
        ]


class CategoryDetailSerializer(serializers.ModelSerializer):
    extension = CategoryExtSerializer()
    topics = serializers.SerializerMethodField()
    total_topics = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "examination_level",
            "block_id",
            "extension",
            "topics",
            "total_topics",
        ]

    def _get_related_topics(self, obj):
        return obj.topics.select_related("extension").all()

    def get_topics(self, obj):
        related_topics = self._get_related_topics(obj)
        topics_dict = {
            topic.block_id: (
                TopicExtSerializer(topic.extension).data
                if hasattr(topic, "extension")
                else {}
            )
            for topic in related_topics
        }
        return topics_dict

    def get_total_topics(self, obj):
        return self._get_related_topics(obj).count()


class VideoResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoResource
        fields = ["id", "title", "url", "duration", "is_featured"]


class BookResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookResource
        fields = ["id", "title", "author", "isbn", "is_featured", "url"]


class ArticleResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleResource
        fields = ["id", "title", "url", "author", "is_featured"]


class TopicExtSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    category_name = serializers.CharField(source="topic.category.name", read_only=True)
    resources = serializers.SerializerMethodField()

    class Meta:
        model = TopicExt
        fields = [
            "topic_name",
            "category_name",
            "description",
            "estimated_duration",
            "metadata",
            "teacher_notes",
            "assessment_criteria",
            "resources",
        ]

    def get_resources(self, obj):
        """
        Safely get all resources handling the case where some might not exist
        """
        try:
            return {
                "videos": VideoResourceSerializer(
                    getattr(obj, "videoresource", []).all(), many=True
                ).data,
                "books": BookResourceSerializer(
                    getattr(obj, "bookresource", []).all(), many=True
                ).data,
                "articles": ArticleResourceSerializer(
                    getattr(obj, "articleresource", []).all(), many=True
                ).data,
            }
        except AttributeError:
            return {"videos": [], "books": [], "articles": []}

from rest_framework import serializers


from .models import SubTopicExt, TopicExt, TopicMastery
from src.apps.core.content.models import Topic


class TopicExtSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)

    class Meta:
        model = TopicExt
        fields = [
            "topic_name",
            "description",
            "base_mastery_points",
            "estimated_hours",
            "teacher_guide",
            "minimum_mastery_percentage",
        ]


class TopicDetailSerializer(serializers.ModelSerializer):
    extension = TopicExtSerializer()
    sub_topics = serializers.SerializerMethodField()
    total_sub_topics = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            "id",
            "name",
            "extension",
            "sub_topics",
            "total_sub_topics",
        ]

    def _get_related_sub_topics(self, obj):
        return obj.subtopic_set.select_related("extension").all()

    def get_sub_topics(self, obj):
        related_sub_topics = self._get_related_sub_topics(obj)
        sub_topics_dict = {
            sub_topic.id: (
                SubTopicExtSerializer(sub_topic.extension).data
                if hasattr(sub_topic, "extension")
                else {}
            )
            for sub_topic in related_sub_topics
        }
        return sub_topics_dict

    def get_total_sub_topics(self, obj):
        return self._get_related_sub_topics(obj).count()


class SubTopicExtSerializer(serializers.ModelSerializer):
    sub_topic_name = serializers.CharField(source="sub_topic.name", read_only=True)
    points_earned = serializers.SerializerMethodField()

    class Meta:
        model = SubTopicExt
        fields = [
            "sub_topic_name",
            "description",
            "estimated_duration",
            "metadata",
            "assessment_criteria",
            "points_earned",
        ]

    def get_points_earned(self, obj):
        request = self.context.get("request")
        if request and request.user:
            try:
                # This assumes there's a way to get from SubTopic to Topic
                # and that TopicMastery tracks points at the Topic level
                topic_mastery = TopicMastery.objects.get(
                    topic=obj.sub_topic.topic, user=request.user
                )
                return topic_mastery.points_earned
            except TopicMastery.DoesNotExist:
                return 0
            except AttributeError:
                # In case the relation path is incorrect
                return 0
        return 0

from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from course_ware.models import Topic

from .models import TopicExt, TopicMastery
from .serializers import TopicDetailSerializer


class TopicDetailView(generics.RetrieveAPIView):
    """
    Retrieve topic details with its extension and subtopics (including their extensions).
    """

    serializer_class = TopicDetailSerializer
    lookup_url_kwarg = "id"

    def get_object(self):
        topic_id = self.kwargs.get(self.lookup_url_kwarg)
        try:
            return (
                Topic.objects.select_related("extension")
                .prefetch_related(
                    "subtopic_set__extension",
                )
                .get(id=topic_id)
            )
        except Topic.DoesNotExist:
            raise NotFound(f"No topic found with ID: {topic_id}")
        except Exception as e:
            raise NotFound(f"Error retrieving topic: {str(e)}")


class UserSubtopicPointsView(APIView):
    """
    Returns a user's points earned and mastery status for a specific subtopic.
    """

    def get(self, request, topic_id, username):
        topic = get_object_or_404(Topic, id=topic_id)
        topic_mastery = get_object_or_404(
            TopicMastery,
            topic=topic,  # Filter topics directly
            user__username=username,
        )
        return Response(
            {
                "points_earned": topic_mastery.points_earned,
                "topic": topic_mastery.topic.name,
                "status": topic_mastery.mastery_status,
            }
        )


class TopicMasteryView(APIView):
    """
    Returns total points earned and possible points for all subtopics in a topic.
    """

    def get(self, request, topic_id, username):
        topic = get_object_or_404(Topic, id=topic_id)

        # Get the user's mastery record for this topic
        topic_mastery = get_object_or_404(
            TopicMastery, topic=topic, user__username=username
        )

        # Get the possible points from the topic extension
        try:
            topic_ext = TopicExt.objects.get(topic=topic)
            possible_points = topic_ext.base_mastery_points
        except TopicExt.DoesNotExist:
            possible_points = 0

        return Response(
            {
                "topic": topic.name,
                "points_earned": topic_mastery.points_earned,
                "possible_points": possible_points,
                "mastery_status": topic_mastery.mastery_status,
                "mastery_status_display": topic_mastery.get_mastery_status_display(),
            }
        )

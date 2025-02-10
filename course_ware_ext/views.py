from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from course_ware.models import Category
from course_ware_ext.models import TopicMastery
from course_ware_ext.serializers import CategoryDetailSerializer


class CategoryDetailView(generics.RetrieveAPIView):
    """
    Retrieve category details with its extension and topics (including their extensions).
    """

    serializer_class = CategoryDetailSerializer
    lookup_url_kwarg = "block_id"

    def get_object(self):
        block_id = self.kwargs.get(self.lookup_url_kwarg)
        try:
            return (
                Category.objects.select_related("extension")
                .prefetch_related(
                    "topics__extension",
                    "topics__extension__videoresource",
                    "topics__extension__bookresource",
                    "topics__extension__articleresource",
                )
                .get(block_id=block_id)
            )
        except Category.DoesNotExist:
            raise NotFound(f"No category found for block ID: {block_id}")
        except Exception as e:
            raise NotFound(f"Error retrieving category: {str(e)}")


class UserTopicPointsView(APIView):
    """
    Returns a user's points earned and mastery status for a specific topic.
    """

    def get(self, request, block_id, username):
        category = get_object_or_404(Category, block_id=block_id)
        topic_mastery = get_object_or_404(
            TopicMastery,
            topic__category=category,  # Filter topics by category
            user__username=username,
        )
        return Response(
            {
                "points_earned": topic_mastery.points_earned,
                "topic": topic_mastery.topic.name,
                "status": topic_mastery.mastery_status,
            }
        )


class CategoryMasteryView(APIView):
    """
    Returns total points earned and possible points for all topics in a category.
    """

    def get(self, request, block_id, username):
        category = get_object_or_404(Category, block_id=block_id)

        total_points = (
            TopicMastery.objects.filter(
                topic__category=category, user__username=username
            ).aggregate(total=Sum("points_earned"))["total"]
            or 0
        )

        possible_points = category.extension.base_mastery_points

        return Response(
            {
                "category": category.name,
                "total_points": total_points,
                "possible_points": possible_points,
            }
        )

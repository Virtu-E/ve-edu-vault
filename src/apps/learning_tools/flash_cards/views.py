from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from course_ware.models import Topic


class FlashcardView(APIView):
    def get(self, request, block_id):
        try:
            topic = get_object_or_404(Topic, block_id=block_id)
            course_key = topic.category.course.course_key

            # question_repo = FlashCardRepoFactory.create_repository(course_key)
            # query = {
            #     "academic_class": topic.category.academic_class.name,
            #     "examination_level": topic.category.examination_level.name,
            #     "topic": topic.name,
            # }
            # flash_cards = question_repo.get_card_collection(query=query)

            # serializer = FlashCardQuestionSerializer(flash_cards, many=True)
            return course_key

            # return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to fetch flashcards: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

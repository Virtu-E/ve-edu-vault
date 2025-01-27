from rest_framework import generics
from rest_framework.exceptions import NotFound

from course_ware.models import Category
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

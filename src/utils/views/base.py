from rest_framework.generics import RetrieveAPIView, UpdateAPIView


class CustomRetrieveAPIView(RetrieveAPIView):
    """
    Custom RetrieveAPIView that overrides the get_object method.

    This view is designed for cases where standard object retrieval
    logic is not needed, allowing for custom response generation without
    relying on a database object.
    """

    def get_object(self):
        """
        Override the default get_object method.

        Returns:
            None: No object retrieval is performed.
        """
        return None


class CustomUpdateAPIView(UpdateAPIView):
    """Custom UpdateAPIView that overrides the get_object method."""

    def get_object(self):
        """
        Override the default get_object method.

        Returns:
            None: No object retrieval is performed.
        """
        return None

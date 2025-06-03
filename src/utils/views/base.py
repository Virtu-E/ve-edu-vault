from typing import Any, Dict, Optional

from adrf.views import APIView


class CustomAPIView(APIView):
    """
    Base API view with serializer support for both sync and async views.
    """

    serializer_class: Optional[Any] = None

    def get_serializer_class(self):
        """Return the serializer class to use."""
        assert self.serializer_class is not None, (
            f"'{self.__class__.__name__}' should either include a `serializer_class` "
            "attribute, or override the `get_serializer_class()` method."
        )
        return self.serializer_class

    def get_serializer(self, *args, **kwargs):
        """Return a serializer instance."""
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def get_serializer_context(self) -> Dict[str, Any]:
        """
        Extra context provided to the serializer class.
        """
        return {"request": self.request, "format": self.format_kwarg, "view": self}

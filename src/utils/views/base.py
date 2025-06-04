from typing import Any, Generic, Optional, Type, TypedDict, TypeVar
from urllib.request import Request

from adrf.views import APIView
from rest_framework.serializers import BaseSerializer


class SerializerContext(TypedDict):
    request: Request
    format: Any
    view: APIView


SerializerType = TypeVar("SerializerType", bound=BaseSerializer)


class CustomAPIView(APIView, Generic[SerializerType]):
    serializer_class: Optional[Type[SerializerType]] = None

    def get_serializer_class(self) -> Type[SerializerType]:
        assert self.serializer_class is not None, (
            f"'{self.__class__.__name__}' should either include a `serializer_class` "
            "attribute, or override the `get_serializer_class()` method."
        )
        return self.serializer_class

    def get_serializer(self, *args, **kwargs) -> SerializerType:
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def get_serializer_context(self) -> SerializerContext:
        return {"request": self.request, "format": self.format_kwarg, "view": self}

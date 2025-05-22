from knox.views import LoginView as KnoxLoginView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from src.apps.core.users.models import EdxUser


class EdxLoginView(KnoxLoginView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        username = request.data.get("username")

        if not username:
            return Response({"error": "Username required"}, status=400)

        try:
            user = EdxUser.objects.get(username=username, active=True)
            request.user = user
            return super().post(request, format)
        except EdxUser.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=401)

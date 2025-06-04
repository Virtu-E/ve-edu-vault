from knox.views import LoginView as KnoxLoginView
from oauth2_provider.contrib.rest_framework import TokenHasScope
from rest_framework.response import Response

from src.apps.core.users.models import EdxUser


class EdxLoginView(KnoxLoginView):
    permission_classes = [TokenHasScope]
    required_scopes = ["edx_login"]

    def post(self, request, format=None):
        username = request.data.get("username")

        if not username:
            return Response({"message": "Username required","error_code" : "400"}, status=400)

        try:
            user = EdxUser.objects.get(username=username, active=True)
            request.user = user
            return super().post(request, format)
        except EdxUser.DoesNotExist:
            return Response({"message": "Invalid credentials", "error_code" : "401"}, status=401)

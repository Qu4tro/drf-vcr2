from typing import Any

import requests
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.mail import EmailMultiAlternatives
from rest_framework import permissions, renderers, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Snippet
from .permissions import IsOwnerOrReadOnly
from .serializers import SnippetSerializer, UserSerializer

User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet[AbstractBaseUser]):
    """
    This viewset automatically provides `list` and `retrieve` actions.
    """

    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer


class SnippetViewSet(viewsets.ModelViewSet[Snippet]):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.

    Additionally we also provide an extra `highlight` action.
    """

    queryset = Snippet.objects.all()
    serializer_class = SnippetSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def highlight(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        snippet = self.get_object()
        return Response(snippet.highlighted)

    def perform_create(self, serializer: serializers.BaseSerializer[Snippet]) -> None:
        serializer.save(owner=self.request.user)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response = super().destroy(request, *args, **kwargs)

        # ip = requests.get("https://google.com").text[:10]
        ip = requests.get("https://api.my-ip.io/ip").text

        email = EmailMultiAlternatives(
            "Snippet deleted",
            f"Snippet {kwargs['pk']} deleted by {request.user.username} from IP {ip}",
            "from@example.com",
            ["to@example.com"],
            ["bcc@example.com"],
            reply_to=["another@example.com"],
        )
        email.attach(
            "views.py",
            # Path(__file__).read_bytes(),
            b"hello world",
            "text/x-script.python",
        )
        email.attach_alternative(
            f"<p>Snippet {kwargs['pk']} deleted by {request.user.username}"
            f"from IP {ip}</p>",
            "text/html",
        )
        email.send()

        return response

from rest_framework import permissions
from djoser.views import UserViewSet as DjoserUserViewSet
from django.contrib.auth import get_user_model

from api.paginations import Pagination
from api.serializers import UserSerializer

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    pagination_class = Pagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return UserSerializer
        return super().get_serializer_class()

from rest_framework import permissions, status
from djoser.views import UserViewSet as DjoserUserViewSet
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.files.storage import default_storage

from api.paginations import Pagination
from api.serializers import UserSerializer, AvatarSerializer

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



    @action(
        detail=False,
        methods=["get"],
        url_path="me",
        permission_classes=[permissions.IsAuthenticated],
    )
    def me(self, request, *args, **kwargs):
        serializer = UserSerializer(
            request.user, context={"request": request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["put"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="me/avatar",
    )
    def upload_avatar(self, request, *args, **kwargs):
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data["avatar"]

        request.user.avatar = data
        request.user.save()

        return Response(
            {"avatar": request.user.avatar.url},
            status=status.HTTP_200_OK
        )

    @upload_avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        if not request.user.avatar:
            return Response(
                {'detail': 'Аватар не найден'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if default_storage.exists(request.user.avatar.path):
                default_storage.delete(request.user.avatar.path)

            request.user.avatar = None
            request.user.save()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response(
                {'detail': f'Ошибка при удалении аватара: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

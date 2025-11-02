from rest_framework import permissions, status
from djoser.views import UserViewSet as DjoserUserViewSet
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.db.models.functions import Lower
from rest_framework.viewsets import ReadOnlyModelViewSet
from django.core.files.storage import default_storage
from django_filters.rest_framework import DjangoFilterBackend

from .paginations import Pagination
from .serializers import (
    UserSerializer, AvatarSerializer, IngSerializer,
    TagSerializer, UserSubSerializer, SubscriptionDeleteSerializer
)
from recipes.models import Tag, Ingredient
from .filters import IngFilter
from users.models import Sub

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngViewSet(ReadOnlyModelViewSet):
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngFilter
    queryset = Ingredient.objects.all().order_by(
        Lower('name')
    )
    serializer_class = IngSerializer


class UserViewSet(DjoserUserViewSet):
    pagination_class = Pagination

    def get_permissions(self):
        data = (permissions.AllowAny(),)
        if self.action == 'list':
            return data
        elif self.action == 'retrieve':
            return data
        return super().get_permissions()

    def get_serializer_class(self):
        data = UserSerializer
        if self.action == 'list':
            return data
        elif self.action == 'retrieve':
            return data
        return super().get_serializer_class()

    @action(
        detail=False,
        methods=('get',),
        url_path='me',
        permission_classes=(permissions.IsAuthenticated,),
    )
    def me(self, request, *args, **kwargs):
        serializer = UserSerializer(
            request.user, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        methods=('put',),
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
        url_path='me/avatar',
    )
    def upload_avatar(self, request, *args, **kwargs):
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data['avatar']

        request.user.avatar = data
        request.user.save()

        url = request.user.avatar.url

        return Response(
            {'avatar': url},
            status=status.HTTP_200_OK
        )

    @upload_avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        if not request.user.avatar:
            raise ValueError('Аватар не найден')

        avatar_path = request.user.avatar.path

        try:
            if default_storage.exists(avatar_path):
                default_storage.delete(avatar_path)
        except (OSError, IOError):
            raise ValidationError('Ошибка при удалении файла аватара')

        request.user.avatar = None
        request.user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete',),
        permission_classes=(permissions.IsAuthenticated,),
        url_path='subscribe',
    )
    def subscribe(self, request, *args, **kwargs):
        author = self.get_object()
        user = request.user
        if request.method == 'POST':
            return self._create_subscription(user, author, request)
        return self._delete_subscription(user, author)

    def _create_subscription(self, user, author, request):
        serializer = UserSubSerializer(
            data={},
            context={
                'request': request,
                'view': self
            }
        )

        serializer.is_valid(raise_exception=True)

        subscription = Sub(user=user, subscribed_to=author)
        subscription.save()

        data = UserSubSerializer(
            author, context={'request': request}
        ).data
        return Response(data, status=status.HTTP_201_CREATED)

    def _delete_subscription(self, user, author):
        serializer = SubscriptionDeleteSerializer(
            data={},
            context={
                'request': self.request,
                'view': self
            }
        )
        serializer.is_valid(raise_exception=True)

        deleted_count, _ = user.subscriptions.filter(
            subscribed_to=author
        ).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(permissions.IsAuthenticated,),
        url_path='subscriptions',
    )
    def subscriptions(self, request, *args, **kwargs):
        queryset = User.objects.filter(subscribers__user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = UserSubSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

from io import BytesIO
from datetime import datetime

from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import (
    decorators,
    permissions,
    status,
    viewsets,
    response
)
from django.urls import reverse

from recipes.models import (
    Recipe,
    Favorite,
    ShoppingCart,
)
from .paginations import Pagination
from .recipes_permissions import IsAuthorOrReadOnly
from .recipes_serializers import (
    RecipeSerializer,
)
from .serializers import SimRecipeSerializer, FavoriteSerializer
from .recipes_filters import RecipeFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly,
    ]
    pagination_class = Pagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @decorators.action(
        detail=True,
        methods=["post"],
        url_name="favorite",
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)

        serializer = FavoriteSerializer(
            data={'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return response.Response(
            SimRecipeSerializer(recipe, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted_count, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()

        if deleted_count == 0:
            return response.Response(
                {'errors': 'Рецепт не найден в избраном'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        detail=True,
        methods=["post"],
        url_name="shopping_cart",
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(
            Recipe,
            id=pk
        )
        instance, created = ShoppingCart.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )

        if not created:
            return response.Response(
                {"errors": "Рецепт корзине уже есть"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SimRecipeSerializer(
            recipe,
            context={'request': request}
        )
        return response.Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        r = get_object_or_404(Recipe, pk=pk)
        count, *args = ShoppingCart.objects.filter(
            user=request.user,
            recipe=r
        ).delete()

        if count == 0:
            return response.Response(
                {'errors': 'НЕТ В КОРЗИНЕ'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        detail=True,
        methods=["get"],
        url_path="get-link"
    )
    def link(self, request, pk=None):
        get_object_or_404(Recipe, id=pk)
        short_url = request.build_absolute_uri(
            reverse('redirect_recipe', kwargs={'pk': pk})
        )
        return response.Response({"short-link": short_url})

    @decorators.action(
        detail=False,
        methods=(
            "get",
        ),
        url_path="download_shopping_cart",
        permission_classes=[permissions.IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        buffer = BytesIO(''.encode('utf-8'))
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f"export_data_{datetime.now()}.txt",
            content_type='text/plain'
        )

from io import BytesIO
from datetime import datetime

from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse
from django.db.models import Sum
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
    ShoppingCart,
    RecipeIng,
    Favorite,
)
from .paginations import Pagination
from .recipes_permissions import IsAuthorOrReadOnly
from .recipes_serializers import (
    RecipeSerializer,
)
from .serializers import SimRecipeSerializer, FavoriteSerializer, \
    ShoppingCartSerializer
from .recipes_filters import RecipeFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly,
    )
    pagination_class = Pagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @staticmethod
    def _add_relation(request, pk, serializer_class, model, relation_name):
        recipe = get_object_or_404(Recipe, id=pk)

        serializer = serializer_class(
            data={'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return response.Response(
            SimRecipeSerializer(recipe, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @staticmethod
    def _remove_relation(request, pk, model):
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted_count, _ = model.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()

        if deleted_count == 0:
            return response.Response(
                {'errors': f'Рецепт не найден в {model._meta.verbose_name}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(
        detail=True,
        methods=["post"],
        url_name="favorite",
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self._add_relation(
            request, pk, FavoriteSerializer, Favorite, 'избранном'
        )

    @favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        return self._remove_relation(request, pk, Favorite)

    @decorators.action(
        detail=True,
        methods=["post"],
        url_name="shopping_cart",
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        return self._add_relation(
            request, pk, ShoppingCartSerializer, ShoppingCart, 'корзине'
        )

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        return self._remove_relation(request, pk, ShoppingCart)

    @decorators.action(
        detail=True,
        methods=('get',),
        url_path='get-link'
    )
    def link(self, request, pk=None):
        get_object_or_404(Recipe, id=pk)
        short_url = request.build_absolute_uri(
            reverse('redirect_recipe', kwargs={'pk': pk})
        )
        return response.Response({'short-link': short_url})

    @decorators.action(
        detail=False,
        methods=(
                'get',
        ),
        url_path='download_shopping_cart',
        permission_classes=(permissions.IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        recipes = Recipe.objects.filter(
            shopping_carts__user=request.user
        ).prefetch_related('recipe_ingredients__ingredient', 'author')

        ingredients = (
            RecipeIng.objects.filter(recipe__in=recipes)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        datetime_str = datetime.now().strftime('%Y%m%d')
        count_of_recipes = len(recipes)
        count_of_ings = len(ingredients)
        report_content = [
            'Список покупок',
            f'Дата составления: {datetime_str}',
            f'Всего рецептов: {count_of_recipes}',
            f'Всего ингредиентов: {count_of_ings}',
            '',
            'Список продуктов:',
            *[
                f'{idx}. {ing["ingredient__name"].title()} - '
                f'{ing["total_amount"]} {ing["ingredient__measurement_unit"]}'
                for idx, ing in enumerate(ingredients, start=1)
            ],
            '',
            'Рецепты:',
            *[
                f'- {recipe.name} (автор: {recipe.author.username})'
                for recipe in recipes
            ]
        ]

        buffer = BytesIO('\n'.join(report_content).encode('utf-8'))
        return FileResponse(
            buffer,
            filename=f'shopping_list_{datetime_str}.txt',
            content_type='text/plain',
            as_attachment=True,
        )

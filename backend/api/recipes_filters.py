from django_filters import rest_framework as df_filters

from recipes.models import Recipe, Tag


class RecipeFilter(df_filters.FilterSet):
    is_in_shopping_cart = df_filters.BooleanFilter(
        method='filter_shopping_cart'
    )
    is_favorited = df_filters.BooleanFilter(
        method='filter_favorites'
    )
    tags = df_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False,
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_in_shopping_cart',
            'is_favorited'
        )

    def filter_shopping_cart(self, queryset, name, recipes):
        if not recipes:
            return queryset

        if self.request.user.is_authenticated:
            return queryset.filter(
                **{'shopping_carts__user': self.request.user})
        return queryset.none()

    def filter_favorites(self, queryset, name, recipes):
        if not recipes:
            return queryset

        if self.request.user.is_authenticated:
            return queryset.filter(**{'favorites__user': self.request.user})
        return queryset.none()

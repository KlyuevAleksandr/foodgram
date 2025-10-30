from django_filters import rest_framework as df_filters

from recipes.models import Ingredient


class IngFilter(df_filters.FilterSet):
    name = df_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = [
            'name',
        ]

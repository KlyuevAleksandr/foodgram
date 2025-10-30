from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import (
    UserSerializer as DjoserUserSerializer
)

from recipes.models import Recipe, Tag, Ingredient, ShoppingCart, Favorite
from users.models import Sub

User = get_user_model()


class IngSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class UserSerializer(DjoserUserSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        if not request.user.is_authenticated:
            return False
        return request.user.subscriptions.filter(subscribed_to=obj).exists()

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'id',
            'email',
            'is_subscribed',
            'avatar'
        )
        read_only_fields = (
            'id',
            'is_subscribed'
        )


class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True)


class SimRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = [
            "id",
            "name",
            "image",
            "cooking_time"
        ]
        read_only_fields = [
            "id",
            "name",
            "image",
            "cooking_time"
        ]


class UserSubSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    class Meta:
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )
        read_only_fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )
        model = User

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        if not request.user.is_authenticated:
            return False
        return request.user.subscriptions.filter(subscribed_to=obj).exists()

    def validate(self, data):
        u = self.context['request'].user
        a = self.context['view'].get_object()

        if u == a:
            raise serializers.ValidationError(
                {
                    'subscribed_to': 'Нельзя подписаться на самого себя'
                }
            )
        if Sub.objects.filter(
                user=u,
                subscribed_to=a
        ).exists():
            raise serializers.ValidationError(
                {'subscribed_to': 'Вы уже подписаны на этого пользователя'}
            )
        else:
            return data

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes = obj.recipes.all()

        try:
            limit = int(request.GET.get("recipes_limit"))
            recipes = recipes[:limit]
        except (ValueError, TypeError):
            pass

        return SimRecipeSerializer(
            recipes, many=True, context=self.context
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        fields = (
            'user',
            'recipe'
        )
        model = Favorite

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f"Рецепт '{recipe.name}' уже в избранном"
            )
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault(),
                                   write_only=True)
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all(),
                                                write_only=True)

    class Meta:
        model = ShoppingCart
        fields = (
            'user',
            'recipe'
        )

    def validate(self, data):
        user, recipe = data['user'], data['recipe']
        in_shop = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if in_shop.exists():
            raise serializers.ValidationError(
                f"Рецепт '{data['recipe'].name}' уже в корзине покупок"
            )
        return data

    def to_representation(self, instance):
        data = SimRecipeSerializer(
            instance.recipe,
            context=self.context
        ).data
        return data

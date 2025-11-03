from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError
from django.core.files.storage import default_storage
from djoser.serializers import (
    UserSerializer as DjoserUserSerializer
)

from recipes.models import Recipe, Tag, Ingredient, ShoppingCart, Favorite
from users.models import Sub

User = get_user_model()


class RemoveRelationSerializer(serializers.Serializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    def validate(self, attrs):
        request = self.context['request']
        recipe = attrs['recipe']
        model = self.context['model']

        relation = model.objects.filter(user=request.user, recipe=recipe)
        if not relation.exists():
            raise serializers.ValidationError(
                f'Рецепт не найден в {model._meta.verbose_name}'
            )
        attrs['relation'] = relation
        return attrs

    def delete_relation(self):
        relation = self.validated_data['relation']
        relation.delete()


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
        request = self.context.get('request')
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
            'is_subscribed',
        )


class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField()


class AvatarDeleteSerializer(serializers.Serializer):

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.avatar:
            raise ValidationError('Аватар не найден')
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        avatar_path = user.avatar.path

        try:
            if default_storage.exists(avatar_path):
                default_storage.delete(avatar_path)
        except (OSError, IOError) as err:
            raise ValidationError('Ошибка при удалении файла аватара') from err

        user.avatar = None
        user.save()
        return user


class SimRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        read_only_fields = (
            'name',
            'image',
            'cooking_time'
        )


class UserSubSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )
        model = User

    def validate(self, data):
        user = self.context['request'].user
        author = self.context['view'].get_object()

        if user == author:
            raise serializers.ValidationError(
                {
                    'subscribed_to': 'Нельзя подписаться на самого себя'
                }
            )
        if Sub.objects.filter(
                user=user,
                subscribed_to=author
        ).exists():
            raise serializers.ValidationError(
                {'subscribed_to': 'Вы уже подписаны на этого пользователя'}
            )
        return data

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        limit = request.GET.get('recipes_limit')
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            pass
        recipes = recipes[:limit]
        return SimRecipeSerializer(
            recipes, many=True, context=self.context
        ).data


class SubscriptionDeleteSerializer(serializers.Serializer):

    def validate(self, attrs):
        request = self.context.get('request')
        view = self.context.get('view')

        if request and view:
            author = view.get_object()
            if not request.user.subscriptions.filter(
                    subscribed_to=author).exists():
                raise serializers.ValidationError('Подписка не найдена.')

        return attrs


class FavoriteShoppingCartSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        fields = ('user', 'recipe')


class FavoriteSerializer(FavoriteShoppingCartSerializer):
    class Meta(FavoriteShoppingCartSerializer.Meta):
        model = Favorite

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Рецепт "{recipe.name}" уже в избранном'
            )
        return data


class ShoppingCartSerializer(FavoriteShoppingCartSerializer):
    class Meta(FavoriteShoppingCartSerializer.Meta):
        model = ShoppingCart
        extra_kwargs = {
            'recipe': {'write_only': True},
            'user': {'write_only': True}
        }

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Рецепт "{recipe.name}" уже в корзине покупок'
            )
        return data

    def to_representation(self, instance):
        return SimRecipeSerializer(
            instance.recipe,
            context=self.context
        ).data

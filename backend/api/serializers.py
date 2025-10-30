from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import (
    UserSerializer as DjoserUserSerializer
)
from recipes.models import Recipe, Tag, Ingredient
from users.models import Subscription

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
        return (
                request and request.user.is_authenticated
                and request.user.subscriptions.filter(subscribed_to=obj).exists()
        )

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


class UserSubSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="recipes.count")

    class Meta(UserSerializer.Meta):
        fields = [
            "id",
            "name",
            "image",
            "cooking_time",
            "recipes",
            "recipes_count"
        ]
        read_only_fields = [
            "id",
            "name",
            "image",
            "cooking_time",
            "recipes",
            "recipes_count"
        ]

    def validate(self, data):
        u = self.context['request'].user
        a = self.context['view'].get_object()

        if u == a:
            raise serializers.ValidationError(
                {
                    'subscribed_to': 'Нельзя подписаться на самого себя'
                }
            )
        if Subscription.objects.filter(
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

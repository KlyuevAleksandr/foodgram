from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import (
    UserSerializer as DjoserUserSerializer
)
from recipes.models import Recipe
from users.models import Subscription


class UserSerializer(DjoserUserSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + ('is_subscribed', 'avatar')
        read_only_fields = ('id', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        return (
            request and request.user.is_authenticated
            and request.user.subscriptions.filter(subscribed_to=obj).exists()
        )

class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True)

class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = fields

class UserSubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="recipes.count")

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("recipes", "recipes_count")
        read_only_fields = fields

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

        return RecipeShortSerializer(
            recipes, many=True, context=self.context
        ).data
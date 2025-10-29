from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import (
    UserSerializer as DjoserUserSerializer
)


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


from django.core.validators import MinValueValidator
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from recipes.models import (
    Recipe,
    RecipeIng,
    Ingredient,
    Tag,
)
from .serializers import UserSerializer, TagSerializer


class RecipeIngSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient.id",
    )
    name = serializers.CharField(
        source="ingredient.name",
        read_only=True,
    )
    amount = serializers.IntegerField(
        validators=[MinValueValidator(1)]
    )
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit",
        read_only=True,
    )

    class Meta:
        fields = (
            "id",
            "name",
            "measurement_unit",
            "amount"
        )
        model = RecipeIng


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(
        read_only=True
    )
    ingredients = RecipeIngSerializer(
        many=True,
        source="recipe_ingredients",
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
    )
    image = Base64ImageField(required=False, allow_null=True)
    cooking_time = serializers.IntegerField(
        validators=[MinValueValidator(1)]
    )
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "tags",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart"
        )

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["tags"] = TagSerializer(
            instance.tags.all(),
            many=True,
        ).data

        return rep

    def validate(self, data):
        tags = data.get('tags', [])
        ingredients = data.get('recipe_ingredients', [])
        image = data.get(
            'image',
        )
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Поле tags не может быть пустым'}
            )
        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                {'tags': 'Дублирование не применимо.'}
            )
        if not ingredients:
            raise serializers.ValidationError(
                {'recipe_ingredients': 'Поле ingredients не может быть пустым'}
            )
        ingredients_ids = [
            ingredient['ingredient']['id'].id for ingredient in ingredients
        ]
        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise serializers.ValidationError(
                {'tags': 'Дублирование не применимо.'}
            )
        if not image:
            raise serializers.ValidationError(
                {'image': 'Изображение нельзя оставить пустым'}
            )

        return data

    @staticmethod
    def _create_recipe_ingredients(recipe, ingredients_data):
        RecipeIng.objects.bulk_create([
            RecipeIng(
                recipe=recipe,
                ingredient=ingredient_data["ingredient"]["id"],
                amount=ingredient_data["amount"],
            )
            for ingredient_data in ingredients_data
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients", [])
        tags_data = validated_data.pop("tags", [])

        recipe = super().create(validated_data)
        recipe.tags.set(tags_data)
        self._create_recipe_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        if 'image' not in validated_data:
            validated_data['image'] = instance.image
        ingredients_data = validated_data.pop("recipe_ingredients", [])
        tags_data = validated_data.pop("tags", [])

        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)
        instance.recipe_ingredients.all().delete()
        self._create_recipe_ingredients(instance, ingredients_data)
        return instance

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        if not request.user.is_authenticated:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        if not request.user.is_authenticated:
            return False
        return obj.shopping_carts.filter(user=request.user).exists()

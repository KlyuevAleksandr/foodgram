from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=256,
        unique=True,
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        unique=True,
        max_length=256,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=128,
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=64,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient',
            ),
        )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Автор',
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=256,
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    image = models.ImageField(
        verbose_name='Изображение блюда',
        upload_to='recipes/images/',
        null=True,
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=(MinValueValidator(1),),
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='RecipeIng',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('name',)
        default_related_name = 'recipes'

    def __str__(self):
        return f'{self.author}) {self.name}'


class RecipeIng(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=(MinValueValidator(1),),
    )

    class Meta:
        verbose_name = 'Ингредиент Р'
        verbose_name_plural = 'Ингредиенты Р'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient',
            ),
        )
        default_related_name = 'recipe_ingredients'

    def __str__(self):
        return f'{self.ingredient} - {self.amount}'


class UserRecipeRelation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s',
            ),
        ]


class Favorite(UserRecipeRelation):
    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorites'

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class ShoppingCart(UserRecipeRelation):
    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_carts'

    def __str__(self):
        return f'Корзина {self.user.username}: {self.recipe.name}'

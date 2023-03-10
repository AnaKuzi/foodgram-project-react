from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()

MIN_VALUE = 1


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(max_length=200,
                            blank=False,
                            unique=True,
                            help_text='Используйте краткое, ключевое слово')
    slug = models.SlugField(max_length=200,
                            blank=False,
                            unique=True,
                            help_text='Создайте уникальную ссылку')
    color = models.CharField(max_length=7,
                             blank=False,
                             unique=True,
                             help_text='Формат - HEX')

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:15]


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(max_length=200,
                            blank=False,
                            help_text='Название ингредиента')
    measurement_unit = models.CharField(max_length=30,
                                        blank=False,
                                        help_text='Сокр. единица измерения',
                                        verbose_name='Единица измерения')

    class Meta:
        ordering = ('name', 'measurement_unit', )
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_measurement_unit_for_ingredient',
            ),
        ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name[:15]}, ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель рецепта."""
    name = models.CharField(max_length=200,
                            blank=False,
                            help_text='Название рецепта')
    text = models.TextField(blank=False, help_text='Описание рецепта')
    cooking_time = models.PositiveIntegerField(
        blank=False,
        help_text='Время приготовления в минутах')
    image = models.ImageField(upload_to="recipes/", blank=False)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               help_text='Автор рецепта',
                               related_name='recipes')
    tags = models.ManyToManyField(Tag, through='RecipeTag')
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient')

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:15]


class RecipeTag(models.Model):
    """Модель сзязи между рецептом и тэгом."""
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='recipe_tags')
    tag = models.ForeignKey(Tag,
                            on_delete=models.CASCADE,
                            related_name='recipe_tags')

    class Meta:
        verbose_name = 'Связь рецепт-тэг'
        verbose_name_plural = 'Связи рецепт-тэг'
        constraints = [models.UniqueConstraint(fields=['tag', 'recipe'],
                       name='unique_tag_recipe')]

    def __str__(self):
        return f'Тэг {self.tag.name[:15]} в рецепте {self.recipe.name[:15]}'


class RecipeIngredient(models.Model):
    """Модель сзязи между рецептом и ингредиентом."""
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='recipeingredient')
    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE,
                                   related_name='recipes')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(MIN_VALUE,
                              message='Количество должно быть больше 0!')
        ]
    )

    class Meta:
        verbose_name = 'Связь рецепт-ингредиент'
        verbose_name_plural = 'Связи рецепт-ингредиент'
        constraints = [models.UniqueConstraint(fields=['ingredient', 'recipe'],
                       name='unique_ingredient_recipe')]

    def __str__(self):
        return (f'Рецепт {self.recipe.name[:15]} влючает {self.amount}',
                f' ингердиента {self.ingredient.name[:15]}')


class FavoriteRecipe(models.Model):
    """Модель избранного рецепта."""
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             help_text='Подписчик',
                             related_name='favorites')
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               help_text='Подписчик',
                               related_name='favorites')

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_users_recipe',
            ),
        ]

    def __str__(self):
        return (f'Пользователь {self.user.username[:15]}',
                f' добавил рецепт {self.recipe.name[:15]} в избранное')

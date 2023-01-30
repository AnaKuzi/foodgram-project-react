import collections.abc

from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, RecipeTag, Tag)
from rest_framework import exceptions, serializers
from shopping_cart.models import ShoppingCart
from users.models import Follow

from .utils import add_recipe_tags_ingredients

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериалайзер для пользователей."""
    password = serializers.CharField(required=True, write_only=True,
                                     max_length=150)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
        )
        read_only_fields = ('id', )


class FollowSerializer(UserSerializer):
    """Сериалайзер для пользователей c подписками"""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
        )
        model = User
        read_only_fields = ('id', )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return Follow.objects.filter(user=user,
                                     author=obj).exists()


class ShowFollowingsSerializer(FollowSerializer):
    """Сериалайзер для вывода подписок"""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed',
                  'recipes', 'recipes_count')
        read_only_fields = fields

    def get_recipes(self, obj):
        request = self.context['request']
        recipe_limit = request.GET.get('recipes_limit')
        if recipe_limit:
            recipes = Recipe.objects.filter(author=obj)[:int(recipe_limit)]
        else:
            recipes = Recipe.objects.filter(author=obj)
        serializer = RecipeSubcribeSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class PasswordChangeSerializer(serializers.Serializer):
    """Сериалайзер изменения пароля."""
    current_password = serializers.CharField(max_length=150)
    new_password = serializers.CharField(max_length=150)

    def validate(self, data):
        if self.context['request'].user.password != data['current_password']:
            raise exceptions.ParseError('Неверный пароль')
        return data


class JWTTokenSerializer(serializers.Serializer):
    """Сериалайзер для получения токена."""
    email = serializers.EmailField()
    password = serializers.CharField(max_length=150)

    def validate(self, data):
        if not User.objects.filter(email=data['email'],
                                   password=data['password']).exists():
            raise exceptions.NotFound('Пользователь не существует')
        return data


class TagSerializer(serializers.ModelSerializer):
    """Сериалайзер для тэга"""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'color')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериалайзер для ингредиента"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeSerializer(serializers.HyperlinkedModelSerializer):
    """Сериалайзер для связи ингредиентов и рецептов"""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit_id'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериалайзер для просмотра рецептов"""
    tags = TagSerializer(many=True)
    author = FollowSerializer()
    ingredients = IngredientRecipeSerializer(
        many=True, source='recipeingredient')
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time')
        read_only_fields = fields

    def get_is_favorited(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return FavoriteRecipe.objects.filter(user=self.context['request'].user,
                                             recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=self.context['request'].user,
                                           recipe=obj).exists()


class RecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для записи рецептов."""
    author = serializers.IntegerField(required=False, write_only=True)
    tags = serializers.ListField(write_only=True)
    ingredients = serializers.ListField(write_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def validate_tags(self, data):
        tags = self.initial_data.get('tags')
        if tags is None:
            raise serializers.ValidationError(
                detail='Необходимо укзать тэги'
            )
        elif (
            isinstance(tags, collections.abc.Sequence) is False
            or len(tags) == 0
        ):
            raise serializers.ValidationError(
                detail='Cписок тегов не валидный'
            )
        return data

    def validate_ingredients(self, data):
        ingredients = []
        for ingredient in data:
            if int(ingredient.get('amount')) < 1:
                raise exceptions.ParseError(
                    'Количество ингредиента должно быть больше нуля')
            if ingredient.get('id') in ingredients:
                raise exceptions.ParseError(
                    'Нельзя дублировать один ингридиент')
            ingredients.append(ingredient.get('id'))
        return data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        add_recipe_tags_ingredients(tags, ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        super().update(instance, validated_data)
        RecipeTag.objects.filter(recipe=instance).delete()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        add_recipe_tags_ingredients(tags, ingredients, instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        serializer = RecipeReadSerializer(
            instance, context={'request': self.context['request']})
        return serializer.data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериалайзер для избранного и списка покупок"""
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image')
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    def validate(self, data):
        request = self.context['request']
        if not request or request.user.is_anonymous:
            return False
        recipe = data['recipe']
        if FavoriteRecipe.objects.filter(user=request.user,
                                         recipe=recipe).exists():
            raise serializers.ValidationError('Этот рецепт уже в избранном')
        return data


class RecipeSubcribeSerializer(serializers.ModelSerializer):
    """Сериалайзер для  вывода рецептов в подписках."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields

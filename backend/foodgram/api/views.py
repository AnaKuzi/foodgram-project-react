from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import FavoriteRecipe, Ingredient, Recipe, Tag
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, SlidingToken
from shopping_cart.models import ShoppingCart
from shopping_cart.serializers import ShoppingCartSerializer
from users.models import Follow

from .filters import IngredientFilter, RecipeFilter
from .pagination import RecipePagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, JWTTokenSerializer,
                          PasswordChangeSerializer, RecipeReadSerializer,
                          RecipeSerializer, ShowFollowingsSerializer,
                          TagSerializer, UserSerializer)

User = get_user_model()


class UserViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                  mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Вьюсет для работы с пользователями."""

    queryset = User.objects.all()
    pagination_class = RecipePagination
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        """
        В зависимости от метода
        возвращает нужный сериалайзер.
        """
        if self.action == 'create':
            return UserSerializer
        return FollowSerializer

    @action(detail=False, methods=['get'],
            url_name='me', permission_classes=(IsAuthenticated,))
    def me(self, request, *args, **kwargs):
        serializer = FollowSerializer(self.request.user,
                                      context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'],
            url_name='set_password', permission_classes=(IsAuthenticated,))
    def set_password(self, request, *args, **kwargs):
        serializer = PasswordChangeSerializer(data=request.data,
                                              context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.password = serializer.data['new_password']
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            url_name='subscriptions', permission_classes=(IsAuthenticated,))
    def subscriptions(self, request, *args, **kwargs):
        queryset = User.objects.filter(following__user=request.user.id)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ShowFollowingsSerializer(
                page, many=True, context={'request': request},)
            return self.get_paginated_response(serializer.data)


class APIToken(generics.CreateAPIView):
    """Вьюкласс для получения токена (регистрации)."""
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = JWTTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User,
            email=serializer.data['email'],
            password=serializer.data['password'])
        return Response(
                {'auth_token': str(SlidingToken.for_user(user))},
                status=status.HTTP_200_OK)


class BlacklistRefresh(generics.CreateAPIView):
    """Вьюкласс для удаления токена."""

    def post(self, request):
        token = RefreshToken(request.data.get('refresh'))
        token.blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowView(generics.CreateAPIView,
                 generics.DestroyAPIView):
    """Вьюкласс для управления подписками."""
    serializer_class = FollowSerializer

    def post(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        Follow.objects.create(user=self.request.user, author=author)
        serializer = ShowFollowingsSerializer(author,
                                              context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        delete_following = Follow.objects.filter(user=self.request.user,
                                                 author=author)
        delete_following.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с тэгами."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами"""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = RecipePagination

    def get_serializer_class(self):
        """
        В зависимости от метода
        возвращает нужный сериалайзер
        """
        if self.action in ('create', 'partial_update'):
            return RecipeSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        current_user = request.user
        try:
            shopping_recipes = Recipe.objects.filter(
                shopping_cart__user=current_user
            )
            name = 'recipeingredient__ingredient__name'
            measurement_unit = 'recipeingredient__ingredient__measurement_unit'
            amount = 'recipeingredient__amount'
            ingredients = shopping_recipes.values(
                name,
                measurement_unit,
                amount
            ).order_by(name)
            total = ingredients.annotate(
                amount=Sum('recipeingredient__amount')
            )
            shopping_cart = 'Список покупок:'
            for ingredient in total:
                shopping_cart += (
                    f"\n- {ingredient[name]}: "
                    f"{ingredient[amount]} "
                    f"{ingredient[measurement_unit]}"
                )
            return HttpResponse(shopping_cart, content_type='text/plain')
        except:
            raise Exception('Список покупок пуст')

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def create_destroy_shopping_cart(self, request, *args, **kwargs):
        if request.method == 'POST':
            data = {
                'user': self.request.user.id,
                'recipe': kwargs.get('pk'),
            }
            serializer = ShoppingCartSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED,
                            headers=headers)
        if request.method == 'DELETE':
            instance = get_object_or_404(ShoppingCart,
                                         user=self.request.user,
                                         recipe=kwargs.get('pk'))
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)


class BaseView(generics.CreateAPIView,
               generics.DestroyAPIView):
    """Базовый вью."""

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.model.objects.create(user=request.user, recipe=recipe)
        return Response(request.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs['recipe_id']
        obj = get_object_or_404(
            self.model, user__id=request.user.id, recipe__id=recipe_id
        )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteView(BaseView):
    """Вьюкласс для избранного."""
    queryset = FavoriteRecipe.objects.all()
    serializer_class = FavoriteSerializer
    model = FavoriteRecipe


class ShoppingCartView(BaseView):
    """Вьюкласс для списка покупок."""
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    model = ShoppingCart

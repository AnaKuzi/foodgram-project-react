from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework_simplejwt.tokens import SlidingToken
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import FavoriteRecipe, Ingredient, Recipe, Tag
from shopping_cart.models import ShoppingCart
from shopping_cart.serializers import ShoppingCartSerializer
from users.models import User, Follow

from .filters import IngredientFilter, RecipeFilter
from .pagination import RecipePagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    FavoriteSerializer,
    FollowSerializer,
    ShowFollowingsSerializer,
    IngredientSerializer,
    RecipeSerializer,
    TagSerializer,
    UserSerializer,
    PasswordChangeSerializer,
    JWTTokenSerializer,
    RecipeReadSerializer,
)


class GetPostViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                     mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Вьюсет для просмотра публикации """


class UserViewSet(GetPostViewSet):
    """Вьюсет для работы с пользователями"""

    queryset = User.objects.all()
    pagination_class = RecipePagination
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserSerializer
        return FollowSerializer

    @action(detail=False, methods=('get',),
            url_name='me', permission_classes=(IsAuthenticated,))
    def me(self, request, *args, **kwargs):
        serializer = FollowSerializer(request.user,
                                      context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=('get',),
            url_name='subscriptions', permission_classes=(IsAuthenticated,))
    def subscriptions(self, request, *args, **kwargs):
        queryset = User.objects.filter(following__user=request.user.id)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ShowFollowingsSerializer(
                page, many=True, context={'request': request},)
            return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=('post',),
            url_name='set_password', permission_classes=(IsAuthenticated,))
    def set_password(self, request, *args, **kwargs):
        serializer = PasswordChangeSerializer(data=request.data,
                                              context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.password = serializer.data['new_password']
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class APIToken(APIView):
    """Вьюкласс для получения токена"""
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = JWTTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User, password=serializer.data['password'],
            email=serializer.data['email'])
        token = SlidingToken.for_user(user)
        return Response(
                {'auth_token': str(token)}, status=status.HTTP_200_OK)


class DeleteToken(APIView):
    """Вьюкласс для удаления токена"""

    def post(self, request):
        token = request.auth
        token.blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowView(APIView):
    """Вьюкласс для управления подписками"""

    def post(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        if Follow.objects.filter(
             user=request.user, author=author).exists():
            return Response(
                {'error': 'Вы уже подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST)
        if author == request.user:
            return Response(
                {'error': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST)
        Follow.objects.create(user=request.user, author=author)
        serializer = ShowFollowingsSerializer(author,
                                              context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        delete_following = Follow.objects.filter(user=request.user,
                                                 author=author)
        if not delete_following.exists():
            return Response(
                {'error': 'Вы не подписаны на этого автора'},
                status=status.HTTP_400_BAD_REQUEST
                )
        delete_following.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с тэгами"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с ингредиентами"""
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
        if self.action == 'create' or self.action == 'partial_update':
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
        user = request.user
        try:
            shopping_recipes = Recipe.objects.filter(
                shopping_cart__user=user
            )
            ingredients = shopping_recipes.values_list(
                'recipeingredient__ingredient__name',
                'recipeingredient__ingredient__measurement_unit',
            ).order_by('recipeingredient__ingredient__name')
            total = ingredients.annotate(
                amount=Sum('recipeingredient__amount')
            )
            shopping_cart = 'Список покупок:'
            for index, ingredient in enumerate(total):
                shopping_cart += (
                    f'\n- {ingredient[0]}: {ingredient[2]} {ingredient[1]}'
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
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers,
            )
        if request.method == 'DELETE':
            instance = get_object_or_404(
                ShoppingCart,
                user=self.request.user,
                recipe=kwargs.get('pk'),
            )
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteView(APIView):
    """Вьюкласс для избранного"""
    MODEL = FavoriteRecipe

    def post(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if self.MODEL.objects.filter(
             user=request.user, recipe=recipe).exists():
            return Response(
                {'error': 'Вы уже добавили этот рецепт'},
                status=status.HTTP_400_BAD_REQUEST
                )
        favorite = self.MODEL.objects.create(user=request.user, recipe=recipe)
        serializer = FavoriteSerializer(favorite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, id=recipe_id)
        deleted = self.MODEL.objects.filter(
            user=request.user, recipe=recipe)
        if not deleted.exists():
            return Response(
                {'error': 'У вас нет этого рецепта'},
                status=status.HTTP_400_BAD_REQUEST)
        deleted.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartView(FavoriteView):
    """Вьюкласс для списка покупок"""
    MODEL = ShoppingCart

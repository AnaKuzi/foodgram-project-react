from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    message = ('Редактировать рецепт может только автор')

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user == obj.author
        )

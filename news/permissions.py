from rest_framework.permissions import BasePermission

from .models import User


class IsReader(BasePermission):
    message = "Reader role required."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.READER


class IsJournalist(BasePermission):
    message = "Journalist role required."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.JOURNALIST


class IsEditor(BasePermission):
    message = "Editor role required."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.EDITOR


class ArticleWritePermission(BasePermission):
    message = "Only editors or the article's journalist author may modify an article."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            User.Role.EDITOR,
            User.Role.JOURNALIST,
        )

    def has_object_permission(self, request, view, obj):
        if request.user.role == User.Role.EDITOR:
            return True
        return obj.author_id == request.user.id

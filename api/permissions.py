from rest_framework.permissions import BasePermission


class HasValidApiKey(BasePermission):
    message = 'API Key válida é necessária.'

    def has_permission(self, request, view):
        return request.auth is not None

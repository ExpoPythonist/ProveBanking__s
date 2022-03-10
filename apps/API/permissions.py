from rest_framework import permissions


class IsClient(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_client


class IsVendor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_vendor


class VendorReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or request.user.is_client

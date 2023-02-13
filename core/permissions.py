from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import APIException
from core.models.user import UserAccount
from core.models.subscription import Subscription

class BettorPermissionOrReadOnly(BasePermission):
    """Permission class to detect if the user is a Bettor

    """
    @staticmethod
    def has_permission(request, view, **kwargs):
        if request.method in SAFE_METHODS:
            return True
        try:
            user_account = UserAccount.objects.get(user=request.user.id)
        except UserAccount.DoesNotExist:
            raise APIException(
                detail='User does not exist',
                code=404
            )
        if not user_account.is_tipster:
            return True
        return False

class  IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        return obj.user.id == request.user.id

class IsOwnerOrSubscriberReadOnly(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Only subscribers can read it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to request of subscribers,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS and obj.user.id == request.user.id:
            return True
        if obj.user.id == request.user.id and request.user.useraccount.is_tipster:
            return True
        
        return False


# TODO: Implement blocked IP
# class BlocklistPermission(BasePermission):
#     """
#     Global permission check for blocked IPs.
#     """

#     def has_permission(self, request, view):
#         ip_addr = request.META['REMOTE_ADDR']
#         blocked = Blocklist.objects.filter(ip_addr=ip_addr).exists()
#         return not blocked

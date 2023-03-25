from rest_framework.permissions import BasePermission, SAFE_METHODS

class  IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        
        return int(obj) == request.user.useraccount.id

class PaystackWebhookPermission(BasePermission):
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def has_permission(self, request, view):
        PAYSTACK_IPS = ['52.31.139.75', '52.49.173.169', '52.214.14.220']
        client_IP = self.get_client_ip(request) in PAYSTACK_IPS
        client_IP in PAYSTACK_IPS



# TODO: Implement blocked IP
# class BlocklistPermission(BasePermission):
#     """
#     Global permission check for blocked IPs.
#     """

#     def has_permission(self, request, view):
#         ip_addr = request.META['REMOTE_ADDR']
#         blocked = Blocklist.objects.filter(ip_addr=ip_addr).exists()
#         return not blocked

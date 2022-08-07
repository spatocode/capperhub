from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_402_PAYMENT_REQUIRED


class ValidationException(APIException):
    status_code = HTTP_400_BAD_REQUEST

class UserAlreadyExistsException(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = _('USER_ALREADY_EXISTS')

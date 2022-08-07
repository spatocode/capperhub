from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_402_PAYMENT_REQUIRED


class ValidationException(APIException):
    status_code = HTTP_400_BAD_REQUEST


class QuotaLimitPaymentException(APIException):
    status_code = HTTP_402_PAYMENT_REQUIRED
    default_detail = _('ACCOUNT_LIMIT_MEET')
    default_code = 'payment_required'


class UserPermissionException(PermissionDenied):
    default_detail = _('USER_PERMISSION_DENIED')
    default_code = 'permission_denied'


class DatabaseException(APIException):
    default_detail = _('DATABASE_EXCEPTION')

class InvalidRequestException(APIException):
    default_detail = _('INVALID_REQUEST_EXCEPTION')

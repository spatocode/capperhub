from rest_framework.exceptions import APIException


class SubscriptionError(APIException):
    status_code = 400

class NotFoundError(APIException):
    status_code = 404

class ForbiddenError(APIException):
    status_code = 403

class PricingError(APIException):
    status_code = 403

class InsuficientFundError(APIException):
    status_code = 403

class BadRequestError(APIException):
    status_code = 400

class PermissionDeniedError(APIException):
    status_code = 401

class RateLimited(ForbiddenError):
    status_code = 403
    default_detail = "Too many requests from user"

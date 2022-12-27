from rest_framework.exceptions import APIException


class SubscriptionError(APIException):
    status_code = 400

class PricingError(APIException):
    status_code = 403

class PaymentSetupError(APIException):
    status_code = 400

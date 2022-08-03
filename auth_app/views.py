from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from auth_app.exceptions import UserAlreadyExistsException, ValidationException
from auth_app.forms import UserAccountForm
from auth_app.models import UserAccount
from rest_framework import views, response, permissions, exceptions
from rest_framework.decorators import permission_classes
from rest_framework.generics import CreateAPIView
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED


@permission_classes((permissions.AllowAny,))
class HealthCheckView(views.APIView):
    def get(self, request, *args, **kwargs):
        return response.Response({"detail": "Health check was successful"})


@permission_classes((permissions.AllowAny,))
class RegisterUserView(views.APIView):
    def post(self, request):
        """
        To create a new user, check will be performed as followings:
        1. Check if user already exists.
        2. Check organization quota (This will be done in `model.clean()`.)
        3. Create temporary slot in local database
        4. Send request to UserStore for inviting user
        5a. (Successful 3) Get back user id for updating the local temporary slot
        5b. (Fail 3) Rollback all data written to local database
        """
        form = UserAccountForm(request.data)
        if not form.is_valid():
            raise ValidationException(_('INCORRECT_DATA'))
        cleaned_data = form.cleaned_data

        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        country = cleaned_data.get('country')
        mobile_no = cleaned_data.get('mobile_no')
        is_predictor = cleaned_data.get('is_predictor')

        try:
            user = User.objects.get(email=email)
            if user:
                raise UserAlreadyExistsException()
        except ObjectDoesNotExist:
            user = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email,
                password=password
            )
            UserAccount.objects.create(
                user=user,
                country=country,
                mobile_no=mobile_no,
                is_predictor=is_predictor
            )
            #TODO: Send an `email verification` email to user

        return response.Response({"detail": "User Creation Successful"}, status=HTTP_201_CREATED)

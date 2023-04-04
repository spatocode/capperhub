from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from rest_framework.decorators import permission_classes
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from core.models.misc import TermsOfUse, PrivacyPolicy, Feedback, Waitlist
from core.serializers import TermsOfUseSerializer, PrivacyPolicySerializer, WaitlistSerializer, FeedbackSerializer

@permission_classes((permissions.AllowAny,))
class TermsOfUseAPIView(APIView):
    def get(self, request):
        terms_of_use = TermsOfUse.objects.all()
        serializer = TermsOfUseSerializer(terms_of_use, many=True)
        return Response(serializer.data)


@permission_classes((permissions.AllowAny,))
class PrivacyPolicyAPIView(APIView):
    def get(self, request):
        privacy_policy = PrivacyPolicy.objects.all()
        serializer = PrivacyPolicySerializer(privacy_policy, many=True)
        return Response(serializer.data)


@permission_classes((permissions.AllowAny,))
class FeedbackAPIView(APIView):
    def post(self, request):
        serializer = FeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@permission_classes((permissions.AllowAny,))
class WaitlistAPIView(APIView):
    def post(self, request):
        serializer = WaitlistSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

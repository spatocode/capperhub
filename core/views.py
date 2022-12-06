import json
from django.contrib.auth.models import User
from django.db.models import Count
from django.http.response import Http404
from rest_framework import authentication
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from dj_rest_auth.registration.views import RegisterView
from core.serializers import SportsTipsSerializer, UserAccountSerializer, UserAccountRegisterSerializer
from core.models.user import UserAccount
from core.models.tips import SportsTips
from core.filters import SportsTipsFilterSet, UserAccountFilterSet
from core.exceptions import SubscriptionError


class CsrfExemptSessionAuthentication(authentication.SessionAuthentication):
    def enforce_csrf(self, request):
        return


class UserAccountRegisterView(RegisterView):
    serializer_class = UserAccountRegisterSerializer

    def perform_create(self, serializer):
        user = super().perform_create(serializer)
        user_account = UserAccount(user=user)
        is_tipster = serializer.data.get('is_tipster')
        if is_tipster:
            user_account.is_tipster = is_tipster
        user_account.save()
        return user


class UserSubscriptionModelViewSet(ModelViewSet):
    serializer_class = UserAccountSerializer

    def get_object(self, pk):
        try:
            return UserAccount.objects.get(pk=pk)
        except UserAccount.DoesNotExist:
            raise Http404

    def get_queryset(self):
        tipster = self.get_object(self.kwargs.get('pk'))
        subscribers = tipster.subscribers.all()
        return subscribers

    def verify_subscription(self, subscriber, tipster):
        if subscriber.is_tipster:
            raise SubscriptionError(
                detail='Subscription by Tipster not permitted',
                code=400
            )

        if not tipster.is_tipster:
            raise SubscriptionError(
                detail='Subscription to non Tipster not permitted',
                code=400
            )

    def subscribe(self, request, pk=None):
        subscriber = self.get_object(pk)
        tipster = self.get_object(request.data.get('tipster'))
        
        self.verify_subscription(subscriber, tipster)
        tipster.subscribers.add(subscriber)
        return Response({"message": "Subscribed successfully"})

    def unsubscribe(self, request, pk=None):
        subscriber = self.get_object(pk)
        tipster = self.get_object(request.data.get('tipster'))
        
        self.verify_subscription(subscriber, tipster)
        tipster.subscribers.remove(subscriber)
        return Response({"message": "Unsubscribed successfully"})


class UserAPIView(APIView):
    filter_class = UserAccountFilterSet

    def get_object(self, pk):
        try:
            return UserAccount.objects.get(pk=pk)
        except UserAccount.DoesNotExist:
            raise Http404

    def get(self, request, pk=None):
        if pk:
            data = self.get_object(pk)
            serializer = UserAccountSerializer(data)
        else:
            query_params = request.query_params
            filterset = self.filter_class(
                data=query_params,
                queryset=UserAccount.objects.all()
                .annotate(num_of_subscribers=Count('subscribers'))
                .defer('subscribers'),
            )
            serializer = UserAccountSerializer(filterset.qs, many=True)

        return Response(serializer.data)
    
    def post(self, request, format=None):
        data = request.data
        serializer = UserAccountSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'User Created Successfully',
            'data': serializer.data
        })
    
    def put(self, request, pk=None, format=None):
        user_account = UserAccount.objects.get(pk=pk)
        serializer = UserAccountSerializer(instance=user_account, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'User updated Successfully',
            'data': serializer.data
        })

    def delete(self, request, pk, format=None):
        user = User.objects.get(pk=pk)
        user.delete()
        return Response({
            'message': 'User deleted Successfully'
        })


class SportsTipsAPIView(APIView):
    filter_class = SportsTipsFilterSet

    def get_object(self, pk):
        try:
            return SportsTips.objects.get(pk=pk)
        except SportsTips.DoesNotExist:
            raise Http404

    def get(self, request, pk=None, format=None):
        if pk:
            data = self.get_object(pk)
            serializer = SportsTipsSerializer(data)
        else:
            query_params = request.query_params
            filterset = self.filter_class(
                data=query_params,
                queryset=SportsTips.objects.all()
            )
            serializer = SportsTipsSerializer(filterset.qs, many=True)

        return Response(serializer.data)

    def put(self, request, pk=None, format=None):
        #TODO: Make sure tips can only be updated before it's sent to subscribers
        tips =  SportsTips.objects.get(pk=pk)
        serializer = SportsTipsSerializer(instance=tips, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Tips updated Successfully',
            'data': serializer.data
        })

    def post(self, request, format=None):
        #TODO: Confirm the match is valid from probably an API before saving to the DB
        data = request.data
        serializer = SportsTipsSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Tips Created Successfully',
            'data': serializer.data
        })

    def delete(self, request, pk, format=None):
        #TODO: Make sure tips can only be deleted before it's sent to subscribers
        try:
            user = SportsTips.objects.get(pk=pk)
        except SportsTips.DoesNotExist:
            raise Http404
        user.delete()
        return Response({
            'message': 'Tips deleted Successfully'
        })

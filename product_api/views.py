from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status, views, generics, response, viewsets, permissions
from rest_framework.decorators import permission_classes

from product_api import filters, serializers
from product_auth_api import serializers as user_serializers
from product_api.exceptions import InvalidRequestException, UserPermissionException
from product_api.models.base import Product


@permission_classes((permissions.IsAuthenticated,))
class ProductView(viewsets.ModelViewSet):
    serializer_class = serializers.ProductSerializer
    product_filterset = filters.ProductFilter

    def get_object(self):
        product = Product.objects.filter()
        return product

    def get_queryset(self):
        query_params = self.request.query_params
        filterset = self.product_filterset(
            data=query_params,
            queryset=self.get_object()
        )
        return filterset.qs

    def create(self, request):
        user = request.user.user_account
        if not user.is_predictor:
            raise UserPermissionException()
        request.data.update({'owner': user.id})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data)


@permission_classes((permissions.IsAuthenticated,))
class ProductInfoView(generics.GenericAPIView):
    serializer_class = serializers.ProductSerializer

    def get_object(self):
        try:
            product = Product.objects.get(id=self.kwargs.get('product_id'))
        except ObjectDoesNotExist:
            product = None
        return product

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return response.Response({}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)


@permission_classes((permissions.IsAuthenticated,))
class ProductSubscriptionView(viewsets.ModelViewSet):
    serializer_class = serializers.ProductSerializer

    def get_object(self):
        try:
            product = Product.objects.get(id=self.kwargs.get('product_id'))
        except ObjectDoesNotExist:
            product = None
        return product

    def subscribe(self, request, *args, **kwargs):
        user = request.user.user_account
        if user.is_predictor:
            raise UserPermissionException()

        instance = self.get_object()
        if not instance:
            return response.Response({}, status=status.HTTP_404_NOT_FOUND)

        user.subscribed_products.add(instance)

        #TODO: Debit user's account for subscription payment

        return response.Response({'detail': 'Subscription successfull'}, status=status.HTTP_201_CREATED)

    def unsubscribe(self, request, *args, **kwargs):
        user = request.user.user_account
        if user.is_predictor:
            raise UserPermissionException()

        instance = self.get_object()
        if not instance:
            return response.Response({}, status=status.HTTP_404_NOT_FOUND)

        user.subscribed_products.remove(instance)

        return response.Response({'detail': 'Unsubscription successfull'}, status=status.HTTP_204_NO_CONTENT)


@permission_classes((permissions.IsAuthenticated,))
class ProductSubscribersView(generics.GenericAPIView):
    serializer_class = user_serializers.UserAccountSerializer

    def get_object(self):
        try:
            product = Product.objects.get(id=self.kwargs.get('product_id'))
        except ObjectDoesNotExist:
            product = None
        return product

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return response.Response({}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance.subscribers.all(), many=True)

        return response.Response(serializer.data)


@permission_classes((permissions.IsAuthenticated,))
class ProductPicksView(viewsets.ModelViewSet):
    serializer_class = serializers.FootballPredictionSerializer

    def get_object(self):
        try:
            product = Product.objects.get(id=self.kwargs.get('product_id'))
        except ObjectDoesNotExist:
            product = None
        return product

    def get_queryset(self):
        instance = self.get_object().football_predictions.all()
        return instance
    
    # def create(self, request):
    #     user = request.user.user_account
    #     if not user.is_predictor:
    #         raise UserPermissionException()
    #     request.data.update({'owner': user.id})
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return response.Response(serializer.data)
    
    # def delete(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     instance.delete()
    #     return response.Response(status=status.HTTP_204_NO_CONTENT)

from django.http.response import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from core.serializers import UserAccountSerializer
from core.models.user import UserAccount


class UserAPIView(APIView):

    def get_object(self, pk):
        try:
            return UserAccount.objects.get(pk=pk)
        except UserAccount.DoesNotExist:
            raise Http404

    def get(self, request, pk=None, format=None):
        if pk:
            data = self.get_object(pk)
            serializer = UserAccountSerializer(data)
        else:
            data = UserAccount.objects.all()
            serializer = UserAccountSerializer(data, many=True)

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
        user = UserAccount.objects.get(pk=pk)
        serializer = UserAccountSerializer(instance=user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'User updated Successfully',
            'data': serializer.data
        })

    def delete(self, request, pk, format=None):
        user = UserAccount.objects.get(pk=pk)
        user.delete()
        return Response({
            'message': 'User deleted Successfully'
        })

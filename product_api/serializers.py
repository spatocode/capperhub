from product_api.models.football import FootballPrediction
from rest_framework import serializers
from product_api.models.base import Currency, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class FootballPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FootballPrediction
        fields = '__all__'

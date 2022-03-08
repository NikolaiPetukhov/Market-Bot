from .models import Product
from rest_framework import serializers


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        id = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
        model = Product
        fields = ['id', 'name', 'price', 'description', 'tags', 'category']

        
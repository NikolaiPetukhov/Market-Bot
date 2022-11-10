from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        id = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
        model = Product
        fields = ["id", "name", "price", "description", "tags"]

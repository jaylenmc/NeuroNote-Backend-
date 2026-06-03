from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import validate_email

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = '__all__'

class NeuroUserSerialzier(serializers.ModelSerializer):
    class Meta:
        fields = ["email", "id", "username"]
        model = get_user_model()

class AuthUserModelSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, min_length=8, max_length=16, write_only=True)
    username = serializers.CharField(max_length=255, required=False)

    def create(self, validated_data):
        user = get_user_model().objects.create_user(**validated_data)
        return user
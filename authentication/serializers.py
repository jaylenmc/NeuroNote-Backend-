from rest_framework import serializers
from django.contrib.auth import get_user_model

class GoogleAuthUserModelSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(validators=[])

    class Meta:
        model = get_user_model()
        fields = ['id','email', 'username']

    def create(self, validated_data):
        obj, created = get_user_model().objects.get_or_create(
            email=validated_data['email'],
            password=None
            )
        return obj

class AuthUserModelSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=True, min_length=8, max_length=16, write_only=True)
    username = serializers.CharField(required=False)
    email = serializers.EmailField(validators=[])
    class Meta:
        model = get_user_model()
        fields = ['id', 'email', 'username', 'password']

    def create(self, validated_data):
        return get_user_model().objects.create_user(**validated_data)
from rest_framework import serializers
from django.conf import settings
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = settings.AUTH_USER_MODEL
        fields = '__all__'

class NeuroUserSerialzier(serializers.ModelSerializer):
    class Meta:
        fields = ["username"]
        model = User
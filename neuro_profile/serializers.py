from rest_framework import serializers

class PresignedUrlPost(serializers.Serializer):
    bucket_name = serializers.CharField(max_length=255)
    object_name = serializers.CharField(max_length=255)
    region_name = serializers.CharField(max_length=255)
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from .services import validate_data
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings

class PresignedUrls(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        validated_data = validate_data(request.data)
        # Generate a presigned S3 POST URL
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_ENDPOINT_URL,
            region_name=validated_data["region_name"],
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'},
            ),
        )
        try:
            response = s3_client.generate_presigned_post(
                validated_data["bucket_name"],
                validated_data["object_name"],
                Fields=None,
                Conditions=None,
                ExpiresIn=3600,
            )
        except ClientError as e:
            return Response({"Client Error": e})

        # The response contains the presigned URL and required fields
        return Response(response, status=status.HTTP_200_OK)
    
    def get(self, request, bucket_name, object_name, region_name):
        # Generate a presigned URL for the S3 object
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_ENDPOINT_URL,
            region_name=region_name,
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'},
            ),
        )
        try:
            response = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=3600,
            )
        except ClientError as e:
            return Response({"Client Error": e})

        # The response contains the presigned URL
        return Response({"url": response}, status=status.HTTP_200_OK)
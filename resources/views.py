from rest_framework.views import APIView, Response
from .serializers import LinkUploadSerializer, FileUploadSerializer, ResourceInputSerializer
from rest_framework import status
from .models import LinkUpload, ResourceTypes, FileUpload
from rest_framework.permissions import IsAuthenticated
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from .services import validate_data
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings

class ImportResource(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id):
        if id:
            link = LinkUpload.objects.filter(user=request.user, id=id).first()
            if link:
                serialzed = LinkUploadSerializer(link)
                return Response(serialzed.data, status=status.HTTP_200_OK)
            return Response({"Error": "Link doesn't exist"}, status=status.HTTP_404_NOT_FOUND)

        links = LinkUpload.objects.filter(user=request.user)
        if links:
            serialized = LinkUploadSerializer(links, many=True)
            return Response(serialized.data, status=status.HTTP_200_OK)
        return Response({"Error": "User has no links"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        print(f"Request data in resources: {request.data}")
        serializer = ResourceInputSerializer(
            data=request.data, 
            context={'method': request.method}
            )
        if serializer.is_valid():
            resource = serializer.save()

            if resource.resource_type.lower() == ResourceTypes.FILE.value:
                serialized = FileUploadSerializer(resource, context={'request': request})
                return Response(serialized.data, status=status.HTTP_201_CREATED)
            
            if resource.resource_type.lower() == ResourceTypes.LINK.value:
                serialized = LinkUploadSerializer(resource, context={"request": request})
                return Response(serialized.data, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, id):
        resource = request.data.get('resource_type').lower()
        if resource not in ResourceTypes.values:
            return Response({"Error": "Invalid resource type"}, status=status.HTTP_400_BAD_REQUEST)
        
        if resource == ResourceTypes.LINK.value:
            link = LinkUpload.objects.filter(user=request.user, id=id).first()
            if link:
                link.delete()
                return Response({"Message": "Link successfully deleted"}, status=status.HTTP_200_OK)
            return Response({"Error": "Link not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if resource in ResourceTypes.values and resource != ResourceTypes.LINK.value:
            file = FileUpload.objects.filter(user=request.user, id=id).first()
            if file:
                file.delete()
                return Response({"Message": "File successfully deleted"}, status=status.HTTP_200_OK)
            return Response({"Error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

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
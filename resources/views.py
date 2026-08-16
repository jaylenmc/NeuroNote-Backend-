from rest_framework.views import APIView, Response
from .serializers import LinkUploadSerializer, PDFUploadSerializer
from rest_framework import status
from .models import LinkUpload, PDFUpload
from rest_framework.permissions import IsAuthenticated
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from django.conf import settings
from resources.models import PinnedResourcesDashboard
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes

class LinkResource(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id):
        # Add error if id isn't included
        if id:
            link = LinkUpload.objects.filter(pr_dashboard__user__user=request.user, id=id)
            if link.exists():
                serialzed = LinkUploadSerializer(link.first())
                return Response(serialzed.data, status=status.HTTP_200_OK)
            return Response({"Error": "Link doesn't exist"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):    
        pr_dashboard = PinnedResourcesDashboard.objects.get(user__user=request.user)
        link_data = LinkUploadSerializer(data=request.data, context={"pr_dashboard": pr_dashboard})
        link_data.is_valid(raise_exception=True)
        link_data.save()
            
        return Response(link_data.data, status=status.HTTP_201_CREATED)
    
    def delete(self, request, id):
        if id:
            link = LinkUpload.objects.filter(pr_dashboard__user__user=request.user, id=id)
            if link.exists():
                link.delete()
                return Response({"Message": "Link successfully deleted"}, status=status.HTTP_200_OK)
            return Response({"Error": "Link not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"Error": "Link ID is required"}, status=status.HTTP_400_BAD_REQUEST)

class PDFResource(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id):
        if id:
            pdf = PDFUpload.objects.filter(pr_dashboard__user__user=request.user, id=id)
            if pdf.exists():
                serialized = PDFUploadSerializer(pdf.first())
                return Response(serialized.data, status=status.HTTP_200_OK)
            return Response({"Error": "PDF doesn't exist"}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, id):
        if id:
            pdf = PDFUpload.objects.filter(pr_dashboard__user__user=request.user, id=id)
            if pdf.exists():
                pdf.delete()
                return Response({"Message": "Link successfully deleted"}, status=status.HTTP_200_OK)
            return Response({"Error": "PDF doesn't exist"}, status=status.HTTP_404_NOT_FOUND)

class PresignedUrls(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            with transaction.atomic():
                pr_dashboard = PinnedResourcesDashboard.objects.get(user__user=request.user)
                pdf_data = PDFUploadSerializer(data=request.data, context={"pr_dashboard": pr_dashboard})
                pdf_data.is_valid(raise_exception=True)
                pdf_data.save()

                # Generate a presigned S3 POST URL
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    endpoint_url=settings.AWS_ENDPOINT_URL,
                    region_name="auto",
                    config=Config(
                        signature_version='s3v4',
                        s3={'addressing_style': 'path'},
                    ),
                )
                try:
                    response = s3_client.generate_presigned_post(
                        "neuro-note-bucket-f-moj-r",
                        pdf_data.data["object_name"],
                        Fields=None,
                        Conditions=None,
                        ExpiresIn=3600,
                    )
                except ClientError as e:
                    return Response({"Client Error": e})
                data = pdf_data.data
                data['url'] = response['url']
                data['fields'] = response['fields']
                return Response(data, status=status.HTTP_201_CREATED)
        # Do more research for better error handling
        except Exception as e:
            return Response({"Error": f"Transaction rolled back -> {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request, object_name):
        if not object_name:
            return Response({"Error": "Bucket name and object name are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate a presigned URL for the S3 object
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_ENDPOINT_URL,
            region_name="auto",
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'},
            ),
        )
        try:
            response = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': "neuro-note-bucket-f-moj-r", 'Key': object_name},
                ExpiresIn=3600,
            )
        except ClientError as e:
            return Response({"Client Error": e})

        # The response contains the presigned URL
        return Response({"url": response}, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def all_resources(request):
    links = LinkUpload.objects.filter(pr_dashboard__user__user=request.user)
    pdfs = PDFUpload.objects.filter(pr_dashboard__user__user=request.user)
    
    if not pdfs.exists() and not links.exists():
        return Response({"Message": "Pinned resources dashboard is empty"})
    
    packaged_data = dict()

    if pdfs.exists():
        pdfs_data = PDFUploadSerializer(pdfs, many=True)
        packaged_data['pdfs'] = pdfs_data.data
    
    if links.exists():
        links_data = LinkUploadSerializer(links, many=True)
        packaged_data['links'] = links_data.data

    return Response(packaged_data, status=status.HTTP_200_OK)
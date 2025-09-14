from rest_framework.views import APIView
from .models import Folder
from .serializers import FolderSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .services import check_content_num
from authentication.models import AuthUser
from .serializers import FolderInputSerializer, FolderPostSerializer

class FolderView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self,request, folder_id=None):  
        if not folder_id:  
            folders = Folder.objects.filter(user=request.user, parent_folder=None).prefetch_related("folder_document")

            for folder in folders:
                folder.content_num = check_content_num(folder.id)
                folder.save()

            serialized = FolderSerializer(folders, many=True)

            return Response({'folders': serialized.data}, status=status.HTTP_200_OK)
        
        folder = Folder.objects.filter(user=request.user, id=folder_id).prefetch_related("folder_document")
        if not folder:
            return Response({'Message': 'Folder not found'}, status=status.HTTP_404_NOT_FOUND)
        folder = folder.first()
        folder.content_num = check_content_num(folder.id)
        folder.save()
        serialized = FolderSerializer(folder)
        return Response(serialized.data, status=status.HTTP_200_OK)
        
    def post(self, request):
        input_serializer = FolderInputSerializer(data=request.data, context={'user': request.user})
        if input_serializer.is_valid():
            folder = input_serializer.save()
            serialized = FolderPostSerializer(folder)
            return Response(serialized.data, status=status.HTTP_201_CREATED)
        return Response({"Error": input_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, id):
        folder = Folder.objects.filter(user=request.user, id=id).first()
        folder.delete()

        return Response({'Message': 'Folder succssesfully deleted'})
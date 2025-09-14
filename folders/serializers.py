from rest_framework import serializers
from .models import Folder
from documents.serializers import FolderDocumentSerializer

class SubFoldersSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'name', 'content_num']
        model = Folder

class FolderSerializer(serializers.ModelSerializer):
    folder_document = FolderDocumentSerializer(many=True)
    sub_folders = SubFoldersSerializer(many=True)
    class Meta:
        fields = ['id', 'name', 'content_num', 'sub_folders', 'folder_document','sub_folders']
        model = Folder
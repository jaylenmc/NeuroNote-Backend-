from rest_framework import serializers
from .models import Folder
from documents.serializers import FolderDocumentSerializer
from .services import check_content_num

class FolderInputSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    parent_folder_id = serializers.PrimaryKeyRelatedField(
        queryset=Folder.objects.all(),
        required=False
    )

    def validate_parent_folder_id(self, value):
        if not Folder.objects.filter(user=self.context['user'], id=value.id).exists():
            raise serializers.ValidationError("Parent folder doesn't exist")
        return value

    def validate_name(self, value):
        if Folder.objects.filter(user=self.context['user'], name=value).exists():
            raise serializers.ValidationError("Folder name already exists")
        return value

    def create(self, validated_data):
        sub_folder = Folder.objects.create(
            name=validated_data['name'],
            user=self.context['user'],
            parent_folder=validated_data.get('parent_folder_id', None)
        )
        return sub_folder

class SubFoldersSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'name', 'content_num', 'parent_folder']
        model = Folder

class FolderSerializer(serializers.ModelSerializer):
    folder_document = FolderDocumentSerializer(many=True)
    sub_folders = SubFoldersSerializer(many=True)
    parent_folder = serializers.SerializerMethodField()

    def get_parent_folder(self, obj):
        if obj.parent_folder:
            return obj.parent_folder.id
        return None

    class Meta:
        fields = ['id', 'name', 'content_num', 'sub_folders', 'folder_document', 'parent_folder']
        model = Folder

class FolderPostSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'name', 'content_num', 'parent_folder']
        model = Folder
from rest_framework import serializers
from .models import PDFUpload, LinkUpload
from rest_framework.exceptions import ValidationError

class LinkUploadSerializer(serializers.ModelSerializer):
    uploaded_at = serializers.DateTimeField(read_only=True)
    resource_type = serializers.CharField(read_only=True)
    class Meta:
        model = LinkUpload
        fields = ["id", 'title', 'link', "resource_type", "uploaded_at"]

    def create(self, value):
        link = LinkUpload.objects.create(
            title=value['title'],
            link=value["link"],
            pr_dashboard=self.context["pr_dashboard"]
        )
        return link
                
class PDFUploadSerializer(serializers.ModelSerializer):
    uploaded_at = serializers.DateTimeField(read_only=True)
    resource_type = serializers.CharField(read_only=True)
    object_name = serializers.CharField()
    class Meta:
        model = PDFUpload
        fields = ["id", "uploaded_at", "resource_type", "object_name"]

    def create(self, value):
        pdf = PDFUpload.objects.create(
            pr_dashboard=self.context["pr_dashboard"],
            object_name=value["object_name"]
            )
        return pdf
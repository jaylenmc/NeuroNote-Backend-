from django.db import models
from folders.models import Folder
from resources.models import PinnedResourcesDashboard

class Document(models.Model):
    class ResourceType(models.TextChoices):
        DOCUMENT_TYPE = "document", "Document"

    title = models.CharField(max_length=255, default="Untitled")
    notes = models.TextField()
    saved = models.DateTimeField(auto_now_add=True)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='folder_document')
    published = models.BooleanField(default=False)
    resource_type = models.CharField(default="Document", max_length=8)
    tag = models.CharField(max_length=255, null=True, blank=True)
    pr_dashboard = models.ForeignKey(PinnedResourcesDashboard, on_delete=models.CASCADE)
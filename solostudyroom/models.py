from django.db import models
from django.conf import settings
from documents.models import Document
from resources.models import FileUpload, LinkUpload

class PinnedResourcesDashboard(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    document = models.ManyToManyField(Document, blank=True)
    file = models.ManyToManyField(FileUpload, blank=True)
    link = models.ManyToManyField(LinkUpload, blank=True)
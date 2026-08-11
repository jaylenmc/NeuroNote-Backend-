from django.db import models
from neuro_profile.models import NeuroProfile

class PinnedResourcesDashboard(models.Model):
    user = models.OneToOneField(NeuroProfile, on_delete=models.CASCADE)

class LinkUpload(models.Model):
    pr_dashboard = models.ForeignKey(PinnedResourcesDashboard, on_delete=models.CASCADE)
    link = models.URLField(max_length=255)
    title = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    resource_type = models.CharField(default="Link", max_length=8)

class PDFUpload(models.Model):
    pr_dashboard = models.ForeignKey(PinnedResourcesDashboard, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    resource_type = models.CharField(default="PDF", max_length=8)

    object_name = models.CharField(max_length=255)
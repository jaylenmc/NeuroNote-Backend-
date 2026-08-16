from django.db import models
from django.conf import settings

class Folder(models.Model):
    name = models.CharField(max_length=255, default='Untitled')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    content_num = models.IntegerField(default=0)
    parent_folder = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='sub_folders',
        null=True, 
        blank=True
    )

class UploadedPDF(models.Model):
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True)

class UploadedTextBook(models.Model):
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True)
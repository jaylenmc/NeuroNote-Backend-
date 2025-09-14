from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from .models import Folder
from documents.models import Document

class FoldersTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.user = User.objects.create(email="test@gmail.com")
        cls.folder = Folder.objects.create(name="Computer Science", user=cls.user)
        cls.sub_folder = Folder.objects.bulk_create([
            Folder(
                name="Java class",
                parent_folder=cls.folder,
                user=cls.user
            ),
            Folder(
                name="Python class",
                parent_folder=cls.folder,
                user=cls.user
            )
        ])
        cls.document = Document.objects.bulk_create([
            Document(
                title="Computer Science",
                notes="In this class we learnign about the basics of programmming",
                published=True,
                folder=cls.folder
            ),
            Document(
                title="Computer Science",
                notes="In this class we learnign about the basics of programmming",
                published=True,
                folder=cls.sub_folder[0]
            ),
  
        ])
    
    def setUp(self):
        self.client.force_authenticate(self.user)

    def test_folders_get(self):
        print('================ Get ================')
        url = reverse("folder-get-post", args=[self.sub_folder[0].pk])
        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response.data}"
        )
        print(response.data, "\n")

    def test_folders_post(self):
        print('================ Post ================')
        url = reverse("folder-get-post")
        data = {
            "name": "Religion Class",
            "parent_folder_id": self.folder.pk
        }
        response = self.client.post(url, data=data)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg=f"Status code error: {response.data}"
        )

        print(response.data, "\n")

    def test_folder_del(self):
        print('================ Delete ================')
        self.folder = Folder.objects.create(name="Gym Class", user=self.user)
        url = reverse("folder-del", args=[self.folder.pk])
        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response.data}"
        )
        self.assertFalse(
            Folder.objects.filter(id=self.folder.pk).exists(),
            msg=f"Folder didnt delete: {response.data}"
        )
        print(response.data, "\n")
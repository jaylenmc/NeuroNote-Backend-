from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from folders.models import Folder
from django.urls import reverse
from rest_framework import status
from .models import Document

class DocumentTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.user = User.objects.create(email="bob@test.com")
        cls.folder = Folder.objects.create(
            name='test_folder',
            user=cls.user
        )

        cls.document = Document.objects.create(
            title = 'Cultural Studies 8/17/25',
            notes = 'Subjectivity\nIts about how to make money online and come to a conclusion about subjectivity and how us as a collective can collaborate together\nBut actually the aliens are coming to America',
            folder = cls.folder,
            published = False
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_document_create(self):
        print("==================== POST Test ====================")
        url = reverse('create-document')
        data = {
            'title': 'Cultural Studies 8/17/25',
            'notes': 'Subjectivity\nIts about how to make money online and come to a conclusion about subjectivity and how us as a collective can collaborate together\nBut actually the aliens are coming to America',
            'folder_id': self.folder.pk,
            'tag': 'Difficult Subject',
            'is_published': False
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=f"Status code error: {response.data}")
        self.assertTrue(Document.objects.filter(folder__user=self.user), msg=f"Document not created: {response.data}")
        print(response.data)

    def test_document_get(self):
        print("==================== GET Test ====================")
        url = reverse('get-all-documents', args=[self.folder.pk])

        response = self.client.get(url, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, 
            msg=f"Status code error: {response.data}"
            )
        print(response.data)

    def test_document_update(self):
        print("==================== PUT Test ====================")
        url = reverse('update-document', args=[self.document.pk])
        data = {
            'title': 'Updated title',
            'notes': 'Subjectivity\nIts about how to make money online and come to a conclusion about subjectivity and how us as a collective can collaborate together\nBut actually the aliens are coming to America',
            'folder_id': self.folder.pk,
            'tag': 'Test tag',
            'is_published': True
        }
        response = self.client.put(url, data=data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK, 
            msg=f"Status code error: {response.data}"
            )
        self.assertNotEqual(
            response.data['title'], self.document.title,
            msg=f"Document didn't update: {response.data}"
            )
        print(response.data)
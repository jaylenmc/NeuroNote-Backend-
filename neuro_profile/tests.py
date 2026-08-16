from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

class FileServeTest(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create(email="fakeemail@gmail.com", username="fakeemail")

    def setUp(self):
        self.client.force_authenticate(self.user)

    def presigned_url_post(self):
        url = reverse("presigned-urls")
        data = {
            "bucket_name": "neuro-note-bucket-f-moj-r",
            "object_name": "SWE Resume",
            "region_name": "us-east-1"
        }

        response = self.client.post(url, data=data, format="json")
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Error: {response.data}"
        )
        print(response.data)

    def presigned_url_get(self):
        url = reverse("presigned-urls", args=["neuro-note-bucket-f-moj-r", "SWE Resume", "us-east-1"])

        response = self.client.get(url, format="json")
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Error: {response.data}"
        )
        print(response.data)
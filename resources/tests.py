from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from .models import LinkUpload, PDFUpload
from resources.models import PinnedResourcesDashboard
from neuro_profile.models import NeuroProfile

class LinkTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create(email='test@gmail.com', username="fakeemail")
        cls.neuro_profile = NeuroProfile.objects.create(user=cls.user)

        cls.pr_dashboard = PinnedResourcesDashboard.objects.create(user=cls.neuro_profile)
        cls.link = LinkUpload.objects.create(
            pr_dashboard=cls.pr_dashboard,
            link="https://docs.djangoproject.com/en/6.0/topics/db/examples/many_to_one/",
            title="django docs"
            )
    
    def setUp(self):
        self.client.force_authenticate(self.user)

    def link_resource_get(self):
        # --- Perfect request ---
        url = reverse("link-get", args=[self.link.id])

        response = self.client.get(url, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"""========================== Link Resource Get (TC: Perfect Request) ==========================\n
            Status Code Error: {response.data}"""
        )
        self.assertTrue(
            all([ele in response.data for ele in ("id", "title", "link", "resource_type", "uploaded_at")]),
            msg=f"""========================== Link Resource Get (TC: Perfect Request) ==========================\n
            One of the keys are missing in response: {response.data}"""
            )
        
        # --- Wrong ID ---
        url2 = reverse("link-get", args=[100])

        response2 = self.client.get(url2, format='json')
        self.assertEqual(
            response2.status_code,
            status.HTTP_404_NOT_FOUND,
            msg=f"""========================== Link Resource Get (TC: Wrong ID) ==========================\n
            Error: {response2.data}"""
        )
        
    def link_resource_post(self):
        # --- Perfect Request ---
        url = reverse("link-post")
        data = {
            "title": "a title to a link",
            "link": "https://www.youtube.com/"
        }

        response = self.client.post(url, data=data, format="json")
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg=f"""========================== Link Resource Post (TC: Perfect Request) ==========================\n
            Error: {response.data}"""
        )
        self.assertTrue(
            all([ele in response.data for ele in ("id", 'title', 'link', "resource_type", "uploaded_at")]),
            msg=f"""========================== Link Resource Post (TC: Perfect Request) ==========================\n
            Missing a key: {response.data}"""
        )
        self.assertTrue(
            LinkUpload.objects.filter(pr_dashboard=self.pr_dashboard, title=data['title'], link=data['link']).exists(),
            msg=f"""========================== Link Resource Post (TC: Perfect Request) ==========================\n
            Object wasn't created: {response.data}"""
        )

        # --- Bad link ---
        bl_data = {
            "title": "a title to a link",
            "link": "htp://youtube.com"
        }
        bl_response = self.client.post(url, data=bl_data, format="json")
        self.assertFalse(
            LinkUpload.objects.filter(pr_dashboard=self.pr_dashboard, title=bl_data['title'], link=bl_data['link']).exists(),
            msg=f"""========================== Link Resource Post (TC: Bad Link) ==========================\n
            Object was created: {bl_response.data}"""
        )
        self.assertEqual(
            bl_response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"""========================== Link Resource Post (TC: Bad Link) ==========================\n
            Status Code Error: {bl_response.data}"""
        )
    
    def link_resource_delete(self):
        # --- Perfect Request ---
        url = reverse("link-get", args=[self.link.id])

        response = self.client.delete(url, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"""========================== Link Resource Delete (TC: Perfect Request) ==========================\n
            Status Code Error: {response.data}"""
        )
        self.assertFalse(
            LinkUpload.objects.filter(pr_dashboard=self.pr_dashboard, title=self.link.title, link=self.link.link).exists(),
            msg=f"""========================== Link Resource Delete (TC: Perfect Request) ==========================\n
            Resource still exists: {response.data}"""
        )

class PDFTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create(email='test@gmail.com', username="fakeemail")
        cls.neuro_profile = NeuroProfile.objects.create(user=cls.user)

        cls.pr_dashboard = PinnedResourcesDashboard.objects.create(user=cls.neuro_profile)
        cls.pdf = PDFUpload.objects.create(
            pr_dashboard=cls.pr_dashboard,
            object_name="SWE Resume"
            )
    
    def setUp(self):
        self.client.force_authenticate(self.user)

    def pdf_resource_get(self):
        # --- Perfect Request ---
        url = reverse("pdf-get-delete", args=[self.pdf.id])

        response = self.client.get(url, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"""========================== PDF Resource Get (TC: Perfect Request) ==========================\n
            Status Code Error: {response.data}"""
        )
        self.assertTrue(
            all([ele in response.data for ele in ("id", "uploaded_at", "resource_type", "object_name")]),
            msg=f"""========================== PDF Resource Get (TC: Perfect Request) ==========================\n
            Missing a key value: {response.data}"""
        )

        # --- Wrong ID ---
        wid_url = reverse("pdf-get-delete", args=[100])

        wid_response = self.client.get(wid_url, format='json')
        self.assertEqual(
            wid_response.status_code,
            status.HTTP_404_NOT_FOUND,
            msg=f"""========================== PDF Resource Get (TC: Wrong ID) ==========================\n
            Status Code Error: {wid_response.data}"""
        )

   
        # --- Perfect Request ---
        url = reverse("pdf-post")
        data = {
            "object_name": "Random Homework Assignment"
        }

        response = self.client.post(url, data=data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg=f"""========================== PDF Resource Post (TC: Perfect Request) ==========================\n
            Status Code Error: {response.data}"""
        )
        self.assertTrue(
            all([ele in response.data for ele in ("id", "uploaded_at", "resource_type", "object_name")]),
            msg=f"""========================== PDf Resource Post (TC: Perfect Request) ==========================\n
            Missing a key value: {response.data}"""
        )
        self.assertTrue(
            PDFUpload.objects.filter(pr_dashboard=self.pr_dashboard, object_name=data["object_name"]).exists(),
            msg=f"""========================== PDF Resource Post (TC: Perfect Request) ==========================\n
            Object wasn't created: {response.data}"""
        )
    
    def pdf_resource_delete(self):
        # --- Perfect Request ---
        url = reverse("pdf-get-delete", args=[self.pdf.id])

        response = self.client.delete(url, format='json')
        self.assertFalse(
            PDFUpload.objects.filter(pr_dashboard=self.pr_dashboard, id=self.pdf.id).exists(),
            msg=f"""========================== PDF Resource Delete (TC: Perfect Request) ==========================\n
            PDF resource didn't delete: {response.data}"""
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"""========================== PDF Resource Delete (TC: Perfect Request) ==========================\n
            Status Code Error: {response.data}"""
        )

        # --- Wrong ID ---
        wid_url = reverse("pdf-get-delete", args=[100])

        wid_response = self.client.delete(wid_url, format='json')
        self.assertEqual(
            wid_response.status_code,
            status.HTTP_404_NOT_FOUND,
            msg=f"""========================== PDF Resource Delete (TC: Wrong ID) ==========================\n
            Status Code Error: {wid_response.data}"""
        )

class FileServeTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create(email="fakeemail@gmail.com", username="fakeemail")
        cls.neuro_profile = NeuroProfile.objects.create(user=cls.user)
        cls.pr_dashboard = PinnedResourcesDashboard.objects.create(user=cls.neuro_profile)

    def setUp(self):
        self.client.force_authenticate(self.user)

    def presigned_url_post(self):
        # --- Perfect Request ---
        url = reverse("presigned-urls-post")
        data = {
            "object_name": "SWE Resume"
        }

        response = self.client.post(url, data=data, format="json")
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg=f"""========================== Presigned Url Post (TC: Perfect Request) ==========================\n
            Status Code Error: {response.data}"""
        )
        self.assertTrue(
            all([ele in response.data for ele in ("id", "uploaded_at", "resource_type", "object_name", "url")]),
            msg=f"""========================== Presigned Url Post (TC: Perfect Request) ==========================\n
            Missing a key value: {response.data}"""
        )
        self.assertTrue(
            PDFUpload.objects.filter(pr_dashboard=self.pr_dashboard, object_name=data["object_name"]).exists(),
            msg=f"""========================== Presigned Url Post (TC: Perfect Request) ==========================\n
            Object wasn't created: {response.data}"""
        )

    def presigned_url_get(self):
        # --- Perfect Request ---
        url = reverse("presigned-urls-get", args=["SWE Resume"])

        response = self.client.get(url, format="json")
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"""========================== Presigned Url Get (TC: Perfect Request) ==========================\n
            Status Code Error: {response.data}"""
        )

class AllResourcesTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create(email="fakeemail@gmail.com", username="fakeemail")
        cls.neuro_profile = NeuroProfile.objects.create(user=cls.user)
        cls.pr_dashboard = PinnedResourcesDashboard.objects.create(user=cls.neuro_profile)
        cls.pdf = PDFUpload.objects.create(
            pr_dashboard=cls.pr_dashboard,
            object_name="SWE Resume"
            )
        cls.link = LinkUpload.objects.create(
            pr_dashboard=cls.pr_dashboard,
            link="https://docs.djangoproject.com/en/6.0/topics/db/examples/many_to_one/",
            title="django docs"
            )


    def setUp(self):
        self.client.force_authenticate(self.user)

    def all_resources_get(self):
        # --- Perfect Request ---
        url = reverse("all-resources")

        response = self.client.get(url, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"""========================== All Resources Get (TC: Perfect Request) ==========================\n
            Status Code Error: {response.data}"""
        )
        print(response.data)
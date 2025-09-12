from django.test import TestCase
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from documents.models import Document
from resources.models import FileUpload, LinkUpload
from folders.models import Folder
from solostudyroom.models import PinnedResourcesDashboard
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
import tempfile
from django.test import override_settings
from flashcards.models import Card, Deck
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django.utils import timezone
from flashcards.models import ReviewLog

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PinnedResourceTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.user = User.objects.create(email="test@gmail.com")

        cls.deck = Deck.objects.bulk_create([
            Deck(
                user=cls.user,
                title='Test Deck',
                subject='Test Subject'
            ),
            Deck(
                user=cls.user,
                title='Test Deck2',
                subject='Test Subject2'
            )
        ])

        cls.cards = Card.objects.bulk_create([
            Card(
                question='How many days are in a week',
                answer='7',
                card_deck=cls.deck[1],
                scheduled_date=(timezone.now() + timedelta(hours=2)).isoformat(),
                last_review_date=(timezone.now() + timedelta(hours=2)).isoformat(),
            ),
            Card(
                question='What is cultural studies?',
                answer='The study of everyday life',
                card_deck=cls.deck[1],
                scheduled_date=(timezone.now() + timedelta(days=2)).isoformat(),
                last_review_date=(timezone.now() + timedelta(days=2)).isoformat(),
            ),
            Card(
                question='How many people are in the world?',
                answer='Billions',
                card_deck=cls.deck[0],
                scheduled_date=(timezone.now() + timedelta(hours=2)).isoformat(),
                last_review_date=(timezone.now() + timedelta(hours=2)).isoformat(),
            ),
            Card(
                question='How do you make pizza?',
                answer='With dough and sauce',
                card_deck=cls.deck[0],
                scheduled_date=(timezone.now() + timedelta(hours=2)).isoformat(),
                last_review_date=(timezone.now() + timedelta(hours=2)).isoformat(),
            ),
        ])

        file = SimpleUploadedFile(
            name="Calc Notes.pdf", 
            content=b"Here are the notes", 
            content_type="content/pdf"
        )

        cls.folder = Folder.objects.create(
            name="Comp Sci", 
            user=cls.user
        )

        cls.document = Document.objects.create(
            title="hello world", 
            notes="Pyhton is a coding language", 
            folder=cls.folder, 
            resource_type="Document"
        )

        cls.link = LinkUpload.objects.create(
            user=cls.user, 
            link="https://www.youtube.com/watch?v=-W89X9GsKyE", 
            resource_type="Link",
            title="Cultural Studies Lecture"
        )

        link = LinkUpload.objects.create(
            user=cls.user, 
            link="https://www.youtube.com/watch?v=-W89X9GsyE", 
            resource_type="Link",
            title="Science lab lecture"
        )
        
        cls.file = FileUpload.objects.create(
            user=cls.user, 
            file_name="Hey Notes", 
            resource_type="PDF", 
            file_upload=file
        )

        cls.pinned_resources = PinnedResourcesDashboard.objects.create(
            user=cls.user, 
        )
        cls.pinned_resources.document.add(cls.document)
        cls.pinned_resources.link.add(cls.link)
        cls.pinned_resources.link.add(link)
        cls.pinned_resources.file.add(cls.file)
    
    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_get_pinned_resources(self):
        print("================ GET TEST ================")
        url = reverse('pinned-resources')
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response.data}"
        )
        print(response.data)
    
    def test_post_pinned_resources(self):
        url = reverse('create-pinned-resource')
        data = {
            'resource_type': 'link',
            'link': 'https://www.youtube.com/watch?v=-W89X9GsyE',
            'title': 'Science lab lecture'
        }

        response = self.client.post(url, data=data, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg=f"Status code error: {response.data}"
        )

        pinned_resource = PinnedResourcesDashboard.objects.filter(
            user=self.user).values_list("document", 'file', 'link')
        
        self.assertTrue(
            pinned_resource.count() > 0,
            msg=f"Pinned resource objects not created: {response.data}"
        )
        print("================ POST TEST ================")
        print(response.data)

    def test_delete_pinned_resources(self):
        test_options = {
            "link": self.link.pk,
            "file": self.file.pk,
            "document": self.document.pk
        }
        
        for key, pk in test_options.items():
            if key == "link":
                print("================ LINK ================")
                url = reverse("delete-resource", args=[pk])
                # url = f"{url}?resource_type=link"

                link_before = PinnedResourcesDashboard.objects.get(user=self.user)
                print(f"- Before call: {link_before.link.all()}")

                response = self.client.delete(url, format='json')
                resources = PinnedResourcesDashboard.objects.get(user=self.user)
                print(f"- After call: {resources.link.all()}")

                self.assertEqual(
                    response.status_code,
                    status.HTTP_200_OK,
                    msg=f"Status code error: {response.data}"
                )
                self.assertNotIn(
                    self.link,
                    resources.link.all(),
                    msg=f"Pinned Resource didn't delete: {response.data}"
                )
                print(response.data)
            
            if key == "file":
                print("================ FILE ================")
                url = reverse("delete-resource", args=[pk])
                url = f"{url}?resource_type=file"

                link_before = PinnedResourcesDashboard.objects.get(user=self.user)
                print(f"- Before call: {link_before.file.all()}")

                response = self.client.delete(url, format='json')
                resources = PinnedResourcesDashboard.objects.get(user=self.user)
                print(f"- After call: {resources.file.all()}")

                self.assertEqual(
                    response.status_code,
                    status.HTTP_200_OK,
                    msg=f"Status code error: {response.data}"
                )
                self.assertNotIn(
                    self.file,
                    resources.file.all(),
                    msg=f"Pinned Resource didn't delete: {response.data}"
                )
                print(response.data)

            if key == "document":
                print("================ DOCUMENT ================")
                url = reverse("delete-resource", args=[pk])
                url = f"{url}?resource_type=document"

                link_before = PinnedResourcesDashboard.objects.get(user=self.user)
                print(f"- Before call: {link_before.document.all()}")

                response = self.client.delete(url, format='json')
                resources = PinnedResourcesDashboard.objects.get(user=self.user)
                print(f"- After call: {resources.document.all()}")

                self.assertEqual(
                    response.status_code,
                    status.HTTP_200_OK,
                    msg=f"Status code error: {response.data}"
                )
                self.assertNotIn(
                    self.document,
                    resources.document.all(),
                    msg=f"Pinned Resource didn't delete: {response.data}"
                )
                print(response.data)

    def test_studyroom_stats(self):
        print("==================== StudyRoom Stats ====================")
        duration1 = timedelta(hours=1, minutes=23, seconds=34)
        duration2 = timedelta(hours=0, minutes=12, seconds=11)
        duration3 = timedelta(hours=0, minutes=30, seconds=43)
        review_logs = ReviewLog.objects.bulk_create([
            ReviewLog(user=self.user, session_time=duration1),
            ReviewLog(user=self.user, session_time=duration2),
            ReviewLog(user=self.user, session_time=duration3)
        ])
        [review_log.cards.add(card) for review_log in review_logs for card in self.cards]

        url = reverse('study-stats')
        url_params = f"{url}?user_timezone=America/Chicago"
        response = self.client.get(url_params)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Status code error: {response.data}"
        )
        print(response.data)
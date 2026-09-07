from unittest.mock import patch

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Article, Newsletter, Publisher, User


class APITestBase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.reader = User.objects.create_user(
            username="reader",
            password="Pass12345!",
            role=User.Role.READER,
            email="reader@example.com",
        )
        self.reader2 = User.objects.create_user(
            username="reader2",
            password="Pass12345!",
            role=User.Role.READER,
            email="reader2@example.com",
        )
        self.journalist = User.objects.create_user(
            username="journalist",
            password="Pass12345!",
            role=User.Role.JOURNALIST,
        )
        self.journalist2 = User.objects.create_user(
            username="journalist2",
            password="Pass12345!",
            role=User.Role.JOURNALIST,
        )
        self.editor = User.objects.create_user(
            username="editor",
            password="Pass12345!",
            role=User.Role.EDITOR,
        )

        self.publisher = Publisher.objects.create(
            name="Pottery Daily",
            description="Independent arts publication.",
        )
        self.publisher.journalists.add(self.journalist)
        self.publisher.editors.add(self.editor)

        self.independent_article = Article.objects.create(
            title="Independent pottery story",
            content="A story about pottery.",
            author=self.journalist,
            approved=True,
            approved_by=self.editor,
        )
        self.publisher_article = Article.objects.create(
            title="Publisher story",
            content="A publisher article.",
            publisher=self.publisher,
            approved=True,
            approved_by=self.editor,
        )


class AuthenticationTests(APITestBase):
    def test_unauthenticated_article_list_is_rejected(self):
        response = self.client.get("/api/articles/")
        self.assertEqual(response.status_code, 401)

    def test_reader_can_view_approved_articles(self):
        self.client.force_authenticate(self.reader)
        response = self.client.get("/api/articles/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)


class SubscriptionTests(APITestBase):
    def test_reader_only_receives_subscribed_content(self):
        self.reader.subscriptions_to_journalists.add(self.journalist)
        self.reader.subscriptions_to_publishers.add(self.publisher)

        self.client.force_authenticate(self.reader)
        response = self.client.get("/api/articles/subscribed/")

        self.assertEqual(response.status_code, 200)
        titles = {article["title"] for article in response.data}
        self.assertEqual(titles, {"Independent pottery story", "Publisher story"})

    def test_reader_without_subscription_receives_no_subscribed_articles(self):
        self.client.force_authenticate(self.reader2)
        response = self.client.get("/api/articles/subscribed/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])


class ArticlePermissionTests(APITestBase):
    def test_journalist_can_create_independent_article(self):
        self.client.force_authenticate(self.journalist)
        response = self.client.post(
            "/api/articles/",
            {"title": "New article", "content": "New content"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        article = Article.objects.get(title="New article")
        self.assertEqual(article.author, self.journalist)
        self.assertIsNone(article.publisher)

    def test_journalist_can_create_publisher_article(self):
        self.client.force_authenticate(self.journalist)
        response = self.client.post(
            "/api/articles/",
            {
                "title": "Publisher article",
                "content": "Publisher content",
                "publisher": self.publisher.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        article = Article.objects.get(title="Publisher article")
        self.assertEqual(article.author, self.journalist)
        self.assertEqual(article.publisher, self.publisher)

    def test_reader_cannot_create_article(self):
        self.client.force_authenticate(self.reader)
        response = self.client.post(
            "/api/articles/",
            {"title": "Not allowed", "content": "Nope"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_journalist_can_update_own_article(self):
        self.client.force_authenticate(self.journalist)
        response = self.client.put(
            f"/api/articles/{self.independent_article.id}/",
            {"title": "Updated", "content": "Updated content"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.independent_article.refresh_from_db()
        self.assertEqual(self.independent_article.title, "Updated")

    def test_journalist_cannot_update_another_journalists_article(self):
        other = Article.objects.create(
            title="Other",
            content="Other content",
            author=self.journalist2,
        )
        self.client.force_authenticate(self.journalist)
        response = self.client.put(
            f"/api/articles/{other.id}/",
            {"title": "No", "content": "No"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_editor_can_delete_article(self):
        self.client.force_authenticate(self.editor)
        response = self.client.delete(f"/api/articles/{self.publisher_article.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Article.objects.filter(id=self.publisher_article.id).exists())


class NewsletterTests(APITestBase):
    def test_journalist_can_create_newsletter(self):
        self.client.force_authenticate(self.journalist)
        response = self.client.post(
            "/api/newsletters/",
            {
                "title": "Weekly Pottery",
                "description": "Curated pottery stories.",
                "articles": [self.independent_article.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Newsletter.objects.filter(title="Weekly Pottery").count(), 1)

    def test_reader_cannot_create_newsletter(self):
        self.client.force_authenticate(self.reader)
        response = self.client.post(
            "/api/newsletters/",
            {
                "title": "Not allowed",
                "description": "Nope",
                "articles": [self.independent_article.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)


class ApprovalIntegrationTests(APITestBase):
    def test_editor_approval_sends_email_and_calls_internal_api(self):
        article = Article.objects.create(
            title="Pending article",
            content="Pending content.",
            author=self.journalist,
        )
        self.reader.subscriptions_to_journalists.add(self.journalist)

        self.client.force_authenticate(self.editor)

        with patch("news.views.requests.post") as mocked_post:
            mocked_post.return_value.raise_for_status.return_value = None

            response = self.client.post(
                reverse("approve_article", kwargs={"pk": article.id})
            )

        self.assertEqual(response.status_code, 302)
        article.refresh_from_db()
        self.assertTrue(article.approved)
        self.assertEqual(article.approved_by, self.editor)
        self.assertEqual(len(mail.outbox), 1)
        mocked_post.assert_called_once()


class ModelValidationTests(APITestBase):
    def test_article_requires_a_journalist_author(self):
        with self.assertRaises(Exception):
            Article.objects.create(
                title="Invalid",
                content="Invalid",
                publisher=self.publisher,
            ).full_clean()

    def test_article_can_have_author_and_publisher(self):
        article = Article(
            title="Publisher article",
            content="Valid",
            author=self.journalist,
            publisher=self.publisher,
        )
        article.full_clean()

    def test_user_roles_exist(self):
        self.assertEqual(User.Role.READER, "reader")
        self.assertEqual(User.Role.EDITOR, "editor")
        self.assertEqual(User.Role.JOURNALIST, "journalist")

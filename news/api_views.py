from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ApprovedArticleLog, Article, Newsletter, Publisher, User
from .permissions import ArticleWritePermission, IsEditor, IsJournalist, IsReader
from .serializers import ArticleSerializer, NewsletterSerializer, PublisherSerializer, UserSerializer


class ArticleListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all approved articles."""
        articles = Article.objects.filter(approved=True).select_related(
            "author", "publisher"
        )
        return Response(
            ArticleSerializer(articles, many=True, context={"request": request}).data
        )

    def post(self, request):
        """Allow a journalist to create an independent or publisher article."""
        if request.user.role != User.Role.JOURNALIST:
            return Response(
                {"detail": "Only journalists can create articles."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ArticleSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        article = serializer.save()
        return Response(
            ArticleSerializer(article, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class SubscribedArticlesAPIView(APIView):
    permission_classes = [IsReader]

    def get(self, request):
        articles = Article.objects.filter(
            approved=True
        ).filter(
            publisher__in=request.user.subscriptions_to_publishers.all()
        ).union(
            Article.objects.filter(
                approved=True,
                author__in=request.user.subscriptions_to_journalists.all(),
            )
        )
        return Response(ArticleSerializer(articles, many=True, context={"request": request}).data)


class ArticleDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Article, pk=pk)

    def get(self, request, pk):
        article = self.get_object(pk)
        if not article.approved and request.user.role != User.Role.EDITOR:
            return Response({"detail": "Article is not approved."}, status=status.HTTP_403_FORBIDDEN)
        return Response(ArticleSerializer(article, context={"request": request}).data)

    def put(self, request, pk):
        article = self.get_object(pk)
        permission = ArticleWritePermission()
        if not permission.has_object_permission(request, self, article):
            return Response({"detail": permission.message}, status=status.HTTP_403_FORBIDDEN)

        serializer = ArticleSerializer(
            article,
            data=request.data,
            context={"request": request},
            partial=False,
        )
        serializer.is_valid(raise_exception=True)

        article.title = serializer.validated_data["title"]
        article.content = serializer.validated_data["content"]
        if "publisher" in serializer.validated_data:
            article.publisher = serializer.validated_data["publisher"]
        article.full_clean()
        article.save()
        return Response(ArticleSerializer(article, context={"request": request}).data)

    def delete(self, request, pk):
        article = self.get_object(pk)
        permission = ArticleWritePermission()
        if not permission.has_object_permission(request, self, article):
            return Response({"detail": permission.message}, status=status.HTTP_403_FORBIDDEN)
        article.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NewsletterListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        newsletters = Newsletter.objects.all().select_related("author").prefetch_related("articles")
        return Response(NewsletterSerializer(
            newsletters, many=True, context={"request": request}
        ).data)

    def post(self, request):
        if request.user.role != User.Role.JOURNALIST:
            return Response(
                {"detail": "Only journalists can create newsletters."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = NewsletterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        newsletter = serializer.save()
        return Response(
            NewsletterSerializer(newsletter, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class PublisherListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        publishers = Publisher.objects.all()
        return Response(PublisherSerializer(publishers, many=True).data)


class UserListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.all()
        return Response(UserSerializer(users, many=True).data)


class ApprovedArticleAPIView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []

    def post(self, request):
        if request.headers.get("X-Internal-API-Key") != __import__(
            "django.conf", fromlist=["settings"]
        ).settings.INTERNAL_API_KEY:
            return Response({"detail": "Invalid internal API key."}, status=status.HTTP_403_FORBIDDEN)

        article_id = request.data.get("article_id")
        article = get_object_or_404(Article, pk=article_id, approved=True)

        log, _ = ApprovedArticleLog.objects.update_or_create(
            article=article,
            defaults={"payload": request.data},
        )

        return Response(
            {"message": "Approved article logged.", "log_id": log.id},
            status=status.HTTP_201_CREATED,
        )

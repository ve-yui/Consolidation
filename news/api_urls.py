from django.urls import path

from .api_views import (
    ApprovedArticleAPIView,
    ArticleDetailAPIView,
    ArticleListCreateAPIView,
    NewsletterListCreateAPIView,
    PublisherListAPIView,
    SubscribedArticlesAPIView,
    UserListAPIView,
)

urlpatterns = [
    path("articles/", ArticleListCreateAPIView.as_view(), name="api_articles"),
    path("articles/subscribed/", SubscribedArticlesAPIView.as_view(), name="api_subscribed_articles"),
    path("articles/<int:pk>/", ArticleDetailAPIView.as_view(), name="api_article_detail"),
    path("newsletters/", NewsletterListCreateAPIView.as_view(), name="api_newsletters"),
    path("publishers/", PublisherListAPIView.as_view(), name="api_publishers"),
    path("users/", UserListAPIView.as_view(), name="api_users"),
    path("approved/", ApprovedArticleAPIView.as_view(), name="api_approved"),
]

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("articles/new/", views.article_create, name="article_create"),
    path("articles/<int:pk>/edit/", views.article_update, name="article_update"),
    path("articles/<int:pk>/delete/", views.article_delete, name="article_delete"),
    path("articles/<int:pk>/approve/", views.approve_article, name="approve_article"),
    path("newsletters/new/", views.newsletter_create, name="newsletter_create"),
    path("newsletters/<int:pk>/edit/", views.newsletter_update, name="newsletter_update"),
    path("newsletters/<int:pk>/delete/", views.newsletter_delete, name="newsletter_delete"),
    path("publishers/", views.publisher_list, name="publisher_list"),
    path("publishers/new/", views.publisher_create, name="publisher_create"),
    path("publishers/<int:pk>/edit/", views.publisher_update, name="publisher_update"),
    path("publishers/<int:pk>/delete/", views.publisher_delete, name="publisher_delete"),
    path("publishers/<int:pk>/subscribe/", views.subscribe_publisher, name="subscribe_publisher"),
    path("journalists/<int:pk>/subscribe/", views.subscribe_journalist, name="subscribe_journalist"),
]

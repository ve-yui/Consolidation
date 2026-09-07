"""Views for the News Application."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
import requests

from .forms import (
    ArticleForm,
    NewsletterForm,
    PublisherForm,
    RegistrationForm,
)
from .models import Article, Newsletter, Publisher, User


def home(request):
    """Display approved content and role-specific actions."""
    articles = Article.objects.filter(approved=True).select_related(
        "author", "publisher"
    )
    pending_articles = (
        Article.objects.filter(approved=False).select_related("author", "publisher")
        if request.user.is_authenticated and request.user.role == User.Role.EDITOR
        else Article.objects.none()
    )
    newsletters = Newsletter.objects.prefetch_related("articles").select_related("author")
    publishers = Publisher.objects.prefetch_related("editors", "journalists")
    journalists = User.objects.filter(role=User.Role.JOURNALIST)
    return render(
        request,
        "home.html",
        {
            "articles": articles,
            "pending_articles": pending_articles,
            "newsletters": newsletters,
            "publishers": publishers,
            "journalists": journalists,
        },
    )


def register(request):
    """Register a public Reader or Journalist account."""
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect("home")
    else:
        form = RegistrationForm()
    return render(request, "register.html", {"form": form})


def editor_required(request):
    """Return a forbidden response unless the current user is an editor."""
    if request.user.role != User.Role.EDITOR:
        return HttpResponseForbidden("Only editors can manage publishers.")
    return None


@login_required
def article_create(request):
    """Allow a journalist to create an article with an optional publisher."""
    if request.user.role != User.Role.JOURNALIST:
        return HttpResponseForbidden("Only journalists can create articles.")
    if request.method == "POST":
        form = ArticleForm(request.POST, user=request.user)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.full_clean()
            article.save()
            messages.success(request, "Article created and sent for editor approval.")
            return redirect("home")
    else:
        form = ArticleForm(user=request.user)
    return render(request, "article_form.html", {"form": form, "title": "Create article"})


@login_required
def article_update(request, pk):
    """Allow editors or the owning journalist to edit an article."""
    article = get_object_or_404(Article, pk=pk)
    if request.user.role not in (User.Role.EDITOR, User.Role.JOURNALIST):
        return HttpResponseForbidden("You do not have permission to edit articles.")
    if request.user.role == User.Role.JOURNALIST and article.author_id != request.user.id:
        return HttpResponseForbidden("Journalists may only edit their own articles.")

    if request.method == "POST":
        form = ArticleForm(request.POST, instance=article, user=request.user)
        if form.is_valid():
            updated = form.save(commit=False)
            if request.user.role == User.Role.JOURNALIST:
                updated.author = request.user
            updated.full_clean()
            updated.save()
            messages.success(request, "Article updated.")
            return redirect("home")
    else:
        form = ArticleForm(instance=article, user=request.user)
    return render(request, "article_form.html", {"form": form, "title": "Edit article"})


@login_required
def article_delete(request, pk):
    """Allow editors or the owning journalist to delete an article."""
    article = get_object_or_404(Article, pk=pk)
    if request.user.role not in (User.Role.EDITOR, User.Role.JOURNALIST):
        return HttpResponseForbidden("You do not have permission to delete articles.")
    if request.user.role == User.Role.JOURNALIST and article.author_id != request.user.id:
        return HttpResponseForbidden("Journalists may only delete their own articles.")
    if request.method == "POST":
        article.delete()
        messages.success(request, "Article deleted.")
        return redirect("home")
    return render(request, "confirm_delete.html", {"object": article, "type": "article"})


@login_required
def approve_article(request, pk):
    """Approve an article, notify matching readers, and call the internal API."""
    if request.user.role != User.Role.EDITOR:
        return HttpResponseForbidden("Only editors can approve articles.")

    article = get_object_or_404(Article, pk=pk)
    if request.method != "POST":
        return render(request, "approve.html", {"article": article})

    if not article.approved:
        article.approved = True
        article.approved_at = timezone.now()
        article.approved_by = request.user
        article.full_clean()
        article.save()

        subscribers = User.objects.filter(role=User.Role.READER).filter(
            Q(subscriptions_to_journalists=article.author)
            | Q(subscriptions_to_publishers=article.publisher)
        ).distinct()
        recipient_emails = [
            email for email in subscribers.values_list("email", flat=True) if email
        ]
        if recipient_emails:
            send_mail(
                subject=f"New approved article: {article.title}",
                message=article.content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_emails,
                fail_silently=False,
            )

        payload = {
            "article_id": article.id,
            "title": article.title,
            "content": article.content,
            "author": article.author.username,
            "publisher": article.publisher.name if article.publisher else None,
            "approved": article.approved,
        }
        try:
            response = requests.post(
                settings.APPROVED_API_URL,
                json=payload,
                headers={"X-Internal-API-Key": settings.INTERNAL_API_KEY},
                timeout=5,
            )
            response.raise_for_status()
            messages.success(
                request,
                "Article approved, subscribers notified, and API log created.",
            )
        except requests.RequestException:
            messages.warning(
                request,
                "Article approved and subscribers notified, but the internal API "
                "log could not be reached.",
            )
    return redirect("home")


@login_required
def newsletter_create(request):
    """Allow a journalist to create a newsletter."""
    if request.user.role != User.Role.JOURNALIST:
        return HttpResponseForbidden("Only journalists can create newsletters.")
    if request.method == "POST":
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.full_clean()
            newsletter.save()
            form.save_m2m()
            messages.success(request, "Newsletter created.")
            return redirect("home")
    else:
        form = NewsletterForm()
    return render(request, "newsletter_form.html", {"form": form})


@login_required
def newsletter_update(request, pk):
    """Allow editors or the owning journalist to edit a newsletter."""
    newsletter = get_object_or_404(Newsletter, pk=pk)
    if request.user.role not in (User.Role.EDITOR, User.Role.JOURNALIST):
        return HttpResponseForbidden("You do not have permission to edit newsletters.")
    if request.user.role == User.Role.JOURNALIST and newsletter.author_id != request.user.id:
        return HttpResponseForbidden("Journalists may only edit their own newsletters.")
    if request.method == "POST":
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.author = newsletter.author
            updated.full_clean()
            updated.save()
            form.save_m2m()
            messages.success(request, "Newsletter updated.")
            return redirect("home")
    else:
        form = NewsletterForm(instance=newsletter)
    return render(request, "newsletter_form.html", {"form": form})


@login_required
def newsletter_delete(request, pk):
    """Allow editors or the owning journalist to delete a newsletter."""
    newsletter = get_object_or_404(Newsletter, pk=pk)
    if request.user.role not in (User.Role.EDITOR, User.Role.JOURNALIST):
        return HttpResponseForbidden("You do not have permission to delete newsletters.")
    if request.user.role == User.Role.JOURNALIST and newsletter.author_id != request.user.id:
        return HttpResponseForbidden("Journalists may only delete their own newsletters.")
    if request.method == "POST":
        newsletter.delete()
        messages.success(request, "Newsletter deleted.")
        return redirect("home")
    return render(
        request, "confirm_delete.html", {"object": newsletter, "type": "newsletter"}
    )


@login_required
def publisher_list(request):
    """Show publishers and their assigned editors and journalists."""
    forbidden = editor_required(request)
    if forbidden:
        return forbidden
    publishers = Publisher.objects.prefetch_related("editors", "journalists")
    return render(request, "publishers.html", {"publishers": publishers})


@login_required
def publisher_create(request):
    """Allow an editor to create a publisher and assign staff."""
    forbidden = editor_required(request)
    if forbidden:
        return forbidden
    if request.method == "POST":
        form = PublisherForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Publisher created and staff assigned.")
            return redirect("publisher_list")
    else:
        form = PublisherForm()
    return render(request, "publisher_form.html", {"form": form, "title": "Create publisher"})


@login_required
def publisher_update(request, pk):
    """Allow an editor to update publisher staff assignments."""
    forbidden = editor_required(request)
    if forbidden:
        return forbidden
    publisher = get_object_or_404(Publisher, pk=pk)
    if request.method == "POST":
        form = PublisherForm(request.POST, instance=publisher)
        if form.is_valid():
            form.save()
            messages.success(request, "Publisher updated.")
            return redirect("publisher_list")
    else:
        form = PublisherForm(instance=publisher)
    return render(request, "publisher_form.html", {"form": form, "title": "Edit publisher"})


@login_required
def publisher_delete(request, pk):
    """Allow an editor to remove a publisher."""
    forbidden = editor_required(request)
    if forbidden:
        return forbidden
    publisher = get_object_or_404(Publisher, pk=pk)
    if request.method == "POST":
        publisher.delete()
        messages.success(request, "Publisher deleted.")
        return redirect("publisher_list")
    return render(request, "confirm_delete.html", {"object": publisher, "type": "publisher"})


@login_required
def subscribe_publisher(request, pk):
    """Subscribe a reader to a publisher."""
    if request.user.role != User.Role.READER:
        return HttpResponseForbidden("Only readers can subscribe.")
    publisher = get_object_or_404(Publisher, pk=pk)
    request.user.subscriptions_to_publishers.add(publisher)
    messages.success(request, f"Subscribed to {publisher.name}.")
    return redirect("home")


@login_required
def subscribe_journalist(request, pk):
    """Subscribe a reader to a journalist."""
    if request.user.role != User.Role.READER:
        return HttpResponseForbidden("Only readers can subscribe.")
    journalist = get_object_or_404(User, pk=pk, role=User.Role.JOURNALIST)
    if journalist != request.user:
        request.user.subscriptions_to_journalists.add(journalist)
    messages.success(request, f"Subscribed to {journalist.username}.")
    return redirect("home")

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        READER = "reader", "Reader"
        EDITOR = "editor", "Editor"
        JOURNALIST = "journalist", "Journalist"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.READER)
    subscriptions_to_publishers = models.ManyToManyField(
        "Publisher",
        blank=True,
        related_name="subscribers",
    )
    subscriptions_to_journalists = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="journalist_subscribers",
    )

    def clean(self):
        super().clean()
        if self.role not in dict(self.Role.choices):
            raise ValidationError({"role": "Select a valid user role."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Publisher(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    editors = models.ManyToManyField(
        User,
        blank=True,
        related_name="managed_publishers",
        limit_choices_to={"role": User.Role.EDITOR},
    )
    journalists = models.ManyToManyField(
        User,
        blank=True,
        related_name="associated_publishers",
        limit_choices_to={"role": User.Role.JOURNALIST},
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="articles_published",
        limit_choices_to={"role": User.Role.JOURNALIST},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    publisher = models.ForeignKey(
        Publisher,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="articles",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="articles_approved",
        limit_choices_to={"role": User.Role.EDITOR},
    )

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if not self.author:
            raise ValidationError({"author": "A journalist must always author the article."})
        if self.author.role != User.Role.JOURNALIST:
            raise ValidationError({"author": "Only journalists can author independent articles."})
        if self.approved and not self.approved_by:
            raise ValidationError({"approved_by": "An approved article must have an editor."})

    def __str__(self):
        return self.title


class Newsletter(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="newsletters_published",
        limit_choices_to={"role": User.Role.JOURNALIST},
    )
    articles = models.ManyToManyField(Article, blank=True, related_name="newsletters")

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if self.author.role != User.Role.JOURNALIST:
            raise ValidationError({"author": "Only journalists can create newsletters."})

    def __str__(self):
        return self.title


class ApprovedArticleLog(models.Model):
    article = models.OneToOneField(Article, on_delete=models.CASCADE)
    received_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(default=dict)

    def __str__(self):
        return f"Approved: {self.article.title}"

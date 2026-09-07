from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Publisher",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, unique=True)),
                ("description", models.TextField(blank=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("username", models.CharField(error_messages={"unique": "A user with that username already exists."}, help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.", max_length=150, unique=True, verbose_name="username")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="email address")),
                ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
                ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.", verbose_name="active")),
                ("date_joined", models.DateTimeField(verbose_name="date joined")),
                ("role", models.CharField(choices=[("reader", "Reader"), ("editor", "Editor"), ("journalist", "Journalist")], default="reader", max_length=20)),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Article",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("content", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("approved", models.BooleanField(default=False)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("approved_by", models.ForeignKey(blank=True, limit_choices_to={"role": "editor"}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="articles_approved", to=settings.AUTH_USER_MODEL)),
                ("author", models.ForeignKey(limit_choices_to={"role": "journalist"}, on_delete=django.db.models.deletion.CASCADE, related_name="articles_published", to=settings.AUTH_USER_MODEL)),
                ("publisher", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="articles", to="news.publisher")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Newsletter",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("author", models.ForeignKey(limit_choices_to={"role": "journalist"}, on_delete=django.db.models.deletion.CASCADE, related_name="newsletters_published", to=settings.AUTH_USER_MODEL)),
                ("articles", models.ManyToManyField(blank=True, related_name="newsletters", to="news.article")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ApprovedArticleLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                ("payload", models.JSONField(default=dict)),
                ("article", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="news.article")),
            ],
        ),
        migrations.AddField(
            model_name="publisher",
            name="editors",
            field=models.ManyToManyField(blank=True, limit_choices_to={"role": "editor"}, related_name="managed_publishers", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="publisher",
            name="journalists",
            field=models.ManyToManyField(blank=True, limit_choices_to={"role": "journalist"}, related_name="associated_publishers", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="user",
            name="groups",
            field=models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups"),
        ),
        migrations.AddField(
            model_name="user",
            name="user_permissions",
            field=models.ManyToManyField(blank=True, related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions"),
        ),
        migrations.AddField(
            model_name="user",
            name="subscriptions_to_journalists",
            field=models.ManyToManyField(blank=True, related_name="journalist_subscribers", symmetrical=False, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="user",
            name="subscriptions_to_publishers",
            field=models.ManyToManyField(blank=True, related_name="subscribers", to="news.publisher"),
        ),
    ]

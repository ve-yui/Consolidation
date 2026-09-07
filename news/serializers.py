from rest_framework import serializers

from .models import Article, Newsletter, Publisher, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "role")


class PublisherSerializer(serializers.ModelSerializer):
    editors = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    journalists = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Publisher
        fields = ("id", "name", "description", "editors", "journalists")


class ArticleSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    publisher = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Article
        fields = (
            "id", "title", "content", "author", "created_at",
            "approved", "publisher", "approved_at",
        )
        read_only_fields = ("author", "created_at", "approved", "approved_at")

    def create(self, validated_data):
        request = self.context["request"]
        article = Article(author=request.user, **validated_data)
        article.full_clean()
        article.save()
        return article

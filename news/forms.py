from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Article, Newsletter, Publisher, User


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")

    def clean_role(self):
        role = self.cleaned_data["role"]
        if role not in (User.Role.READER, User.Role.JOURNALIST):
            raise forms.ValidationError(
                "Public registration is limited to Reader and Journalist accounts."
            )
        return role


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ("title", "content", "publisher")
        widgets = {"content": forms.Textarea(attrs={"rows": 10})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned = super().clean()
        if self.user and self.user.role == User.Role.JOURNALIST:
            cleaned["author"] = self.user
        return cleaned


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ("title", "description", "articles")
        widgets = {"articles": forms.CheckboxSelectMultiple}


class PublisherForm(forms.ModelForm):
    class Meta:
        model = Publisher
        fields = ("name", "description", "editors", "journalists")
        widgets = {
            "editors": forms.CheckboxSelectMultiple,
            "journalists": forms.CheckboxSelectMultiple,
        }

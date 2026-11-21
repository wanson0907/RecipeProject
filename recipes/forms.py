from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Comment, Recipe


class BootstrapMixin:
    """모든 입력창에 Bootstrap 스타일(form-control)을 자동으로 붙여줍니다."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class RecipeForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ["title", "description", "image", "ingredients", "steps"]
        widgets = {
            "ingredients": forms.Textarea(attrs={"rows": 6}),
            "steps": forms.Textarea(attrs={"rows": 8}),
        }


class CommentForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        labels = {"content": ""}
        widgets = {
            "content": forms.Textarea(
                attrs={"rows": 2, "placeholder": "댓글을 입력하세요"}
            )
        }


class SignupForm(BootstrapMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "password1", "password2"]

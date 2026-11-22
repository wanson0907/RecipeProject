from django import forms
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
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

    def clean_image(self):
        """새로 올린 사진이 너무 크면 거절합니다. (기존 사진은 검사하지 않습니다)"""
        image = self.cleaned_data.get("image")
        max_mb = getattr(settings, "MAX_IMAGE_UPLOAD_MB", 5)
        if isinstance(image, UploadedFile) and image.size > max_mb * 1024 * 1024:
            raise forms.ValidationError(
                f"사진은 {max_mb}MB 이하만 올릴 수 있어요. (지금 {image.size / 1024 / 1024:.1f}MB)"
            )
        return image


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

from django.conf import settings
from django.db import models
from django.urls import reverse


class Recipe(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipes"
    )
    title = models.CharField("제목", max_length=100)
    description = models.CharField("한 줄 소개", max_length=200, blank=True)
    ingredients = models.TextField("재료", help_text="한 줄에 재료 하나씩 적어주세요")
    steps = models.TextField("만드는 법", help_text="한 줄에 한 단계씩 적어주세요")
    image = models.ImageField("대표 사진", upload_to="recipes/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("recipe_detail", args=[self.pk])

    def ingredient_list(self):
        return [line.strip() for line in self.ingredients.splitlines() if line.strip()]

    def step_list(self):
        return [line.strip() for line in self.steps.splitlines() if line.strip()]


class Comment(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField("댓글", max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author} - {self.content[:20]}"


class Like(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["recipe", "user"], name="unique_like")
        ]

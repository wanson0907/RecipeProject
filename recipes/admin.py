from django.contrib import admin

from .models import Comment, Like, Recipe

admin.site.register(Recipe)
admin.site.register(Comment)
admin.site.register(Like)

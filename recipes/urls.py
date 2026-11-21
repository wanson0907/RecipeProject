from django.urls import path

from . import views

urlpatterns = [
    path("", views.RecipeListView.as_view(), name="recipe_list"),
    path("recipes/new/", views.RecipeCreateView.as_view(), name="recipe_create"),
    path("recipes/<int:pk>/", views.recipe_detail, name="recipe_detail"),
    path("recipes/<int:pk>/edit/", views.RecipeUpdateView.as_view(), name="recipe_update"),
    path("recipes/<int:pk>/delete/", views.RecipeDeleteView.as_view(), name="recipe_delete"),
    path("recipes/<int:pk>/comments/", views.comment_create, name="comment_create"),
    path("comments/<int:pk>/delete/", views.comment_delete, name="comment_delete"),
    path("recipes/<int:pk>/like/", views.like_toggle, name="like_toggle"),
    path("api/chatbot/", views.chatbot_api, name="chatbot_api"),
    path("mypage/", views.mypage, name="mypage"),
    path("signup/", views.signup, name="signup"),
]

import json
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import CommentForm, RecipeForm, SignupForm
from .models import Comment, Like, Recipe
from .services import ask_gemini_chef


class RecipeListView(ListView):
    model = Recipe
    template_name = "recipes/recipe_list.html"
    context_object_name = "recipes"
    paginate_by = 9

    def get_queryset(self):
        qs = Recipe.objects.select_related("author").annotate(like_count=Count("likes"))
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(ingredients__icontains=q)
                | Q(description__icontains=q)
            )
        if self.request.GET.get("sort") == "popular":
            return qs.order_by("-like_count", "-created_at")
        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["sort"] = self.request.GET.get("sort", "")
        # 메인 화면 상단에 추천 수 기준 베스트 레시피 TOP 10을 노출합니다.
        # 검색 중에도 전체 베스트 목록은 유지해 사이트의 인기 레시피를 보여줍니다.
        ctx["best_recipes"] = (
            Recipe.objects.select_related("author")
            .annotate(like_count=Count("likes"))
            .filter(like_count__gt=0)
            .order_by("-like_count", "-created_at")[:10]
        )
        return ctx


def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe.objects.select_related("author"), pk=pk)
    liked = (
        request.user.is_authenticated
        and recipe.likes.filter(user=request.user).exists()
    )
    return render(
        request,
        "recipes/recipe_detail.html",
        {
            "recipe": recipe,
            "comments": recipe.comments.select_related("author"),
            "comment_form": CommentForm(),
            "like_count": recipe.likes.count(),
            "liked": liked,
        },
    )


class RecipeCreateView(LoginRequiredMixin, CreateView):
    model = Recipe
    form_class = RecipeForm
    template_name = "recipes/recipe_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class AuthorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.get_object().author == self.request.user


class RecipeUpdateView(AuthorRequiredMixin, UpdateView):
    model = Recipe
    form_class = RecipeForm
    template_name = "recipes/recipe_form.html"


class RecipeDeleteView(AuthorRequiredMixin, DeleteView):
    model = Recipe
    template_name = "recipes/recipe_confirm_delete.html"
    success_url = reverse_lazy("recipe_list")


@login_required
@require_POST
def comment_create(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.recipe = recipe
        comment.author = request.user
        comment.save()
    else:
        messages.error(request, "댓글 내용을 입력해주세요.")
    return redirect("recipe_detail", pk=pk)


@login_required
@require_POST
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    recipe_pk = comment.recipe_id
    comment.delete()
    return redirect("recipe_detail", pk=recipe_pk)


@login_required
@require_POST
def like_toggle(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    like, created = Like.objects.get_or_create(recipe=recipe, user=request.user)
    if not created:
        like.delete()
    return redirect("recipe_detail", pk=pk)


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("recipe_list")
    else:
        form = SignupForm()
    return render(request, "registration/signup.html", {"form": form})


# 한 사람이 하루에 챗봇에게 질문할 수 있는 최대 횟수
CHATBOT_DAILY_LIMIT = 10


def _use_chatbot_quota(user):
    """
    오늘 사용 횟수를 1 늘리고 (허용 여부, 남은 횟수)를 돌려줍니다.
    날짜(한국 시간 기준)가 바뀌면 새 키가 만들어져서 자동으로 0부터 다시 시작합니다.
    """
    key = f"chatbot_count:{user.pk}:{timezone.localdate().isoformat()}"
    cache.add(key, 0, timeout=60 * 60 * 24)  # 키가 없을 때만 0으로 만들기
    count = cache.incr(key)
    if count > CHATBOT_DAILY_LIMIT:
        return False, 0
    return True, CHATBOT_DAILY_LIMIT - count


@require_POST
def chatbot_api(request):
    """
    사용자의 메시지를 받아 Gemini API를 통해 음식 및 레시피를 추천해주는 API 엔드포인트입니다.
    로그인한 사용자만 쓸 수 있고, 한 사람당 하루 CHATBOT_DAILY_LIMIT번까지 가능합니다.
    """
    # 로그인 확인 (fetch 요청이라 로그인 페이지로 이동시키지 않고 JSON으로 안내합니다)
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "AI 셰프는 로그인한 회원만 이용할 수 있어요. 로그인 후 다시 질문해 주세요!"},
            status=401,
        )

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "잘못된 JSON 형식입니다."}, status=400)

    message = data.get("message", "").strip()
    history = data.get("history", [])

    if not message:
        return JsonResponse({"error": "메시지를 입력해주세요."}, status=400)

    # 하루 횟수 제한 확인
    allowed, remaining = _use_chatbot_quota(request.user)
    if not allowed:
        return JsonResponse(
            {
                "error": f"오늘 AI 셰프 질문 {CHATBOT_DAILY_LIMIT}회를 모두 사용했어요. "
                "내일 다시 이용해 주세요! 그동안 사이트의 레시피를 직접 둘러보셔도 좋아요 🍳"
            },
            status=429,
        )

    result = ask_gemini_chef(message, history=history)
    result["remaining"] = remaining
    return JsonResponse(result)


@login_required
def mypage(request):
    """
    로그인한 사용자의 마이페이지: 작성한 레시피, 좋아요한 레시피, 작성한 댓글 목록을 조회합니다.
    """
    user = request.user
    my_recipes = (
        Recipe.objects.filter(author=user)
        .annotate(like_count=Count("likes"))
        .order_by("-created_at")
    )
    liked_recipes = (
        Recipe.objects.filter(likes__user=user)
        .annotate(like_count=Count("likes"))
        .order_by("-likes__id")
    )
    my_comments = (
        Comment.objects.filter(author=user)
        .select_related("recipe")
        .order_by("-created_at")
    )

    context = {
        "my_recipes": my_recipes,
        "liked_recipes": liked_recipes,
        "my_comments": my_comments,
        "my_recipes_count": my_recipes.count(),
        "liked_recipes_count": liked_recipes.count(),
        "my_comments_count": my_comments.count(),
    }
    return render(request, "recipes/mypage.html", context)



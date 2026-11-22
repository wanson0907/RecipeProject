from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from recipes.auth_views import ThrottledLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    # 로그인은 실패 횟수를 제한하는 화면을 먼저 연결합니다 (아래 include보다 위에 있어야 합니다)
    path("accounts/login/", ThrottledLoginView.as_view(), name="login"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("recipes.urls")),
    # 업로드된 사진(로컬 저장 시)을 DEBUG=False(배포) 환경에서도 보여줍니다.
    # Cloudinary를 쓰면 사진 주소가 Cloudinary 주소라 이 경로는 쓰이지 않습니다.
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]

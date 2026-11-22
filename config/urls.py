from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("recipes.urls")),
    # 업로드된 사진(로컬 저장 시)을 DEBUG=False(배포) 환경에서도 보여줍니다.
    # Cloudinary를 쓰면 사진 주소가 Cloudinary 주소라 이 경로는 쓰이지 않습니다.
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]

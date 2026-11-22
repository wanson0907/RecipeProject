import hashlib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.core.cache import cache


class ThrottledLoginView(LoginView):
    """
    같은 아이디로 로그인에 연속 실패하면 잠시 로그인을 막는 로그인 화면입니다.
    (비밀번호를 계속 바꿔 가며 맞춰보는 공격을 어렵게 합니다)
    횟수와 시간은 settings.py 의 LOGIN_MAX_ATTEMPTS, LOGIN_LOCK_SECONDS 로 바꿀 수 있습니다.
    """

    @property
    def max_attempts(self):
        return getattr(settings, "LOGIN_MAX_ATTEMPTS", 5)

    @property
    def lock_seconds(self):
        return getattr(settings, "LOGIN_LOCK_SECONDS", 300)

    def _key(self):
        username = self.request.POST.get("username", "").strip().lower()
        digest = hashlib.sha256(username.encode("utf-8")).hexdigest()[:32]
        return f"login_fail:{digest}"

    def post(self, request, *args, **kwargs):
        # 이미 잠긴 상태면 비밀번호 확인 없이 바로 거절합니다
        if cache.get(self._key(), 0) >= self.max_attempts:
            minutes = max(1, self.lock_seconds // 60)
            messages.error(
                request,
                f"로그인에 너무 많이 실패해서 잠시 막았어요. {minutes}분 뒤에 다시 시도해 주세요.",
            )
            form = self.get_form_class()(request=request)
            return self.render_to_response(self.get_context_data(form=form), status=429)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        # 로그인 실패 횟수를 1 늘립니다
        key = self._key()
        cache.add(key, 0, timeout=self.lock_seconds)
        try:
            count = cache.incr(key)
        except ValueError:
            cache.set(key, 1, timeout=self.lock_seconds)
            count = 1
        remaining = self.max_attempts - count
        minutes = max(1, self.lock_seconds // 60)
        if remaining <= 0:
            messages.error(request=self.request, message=f"로그인에 너무 많이 실패했어요. {minutes}분 동안 로그인이 막힙니다.")
        elif remaining <= 2:
            messages.warning(self.request, f"{remaining}번 더 실패하면 {minutes}분 동안 로그인이 막혀요.")
        return super().form_invalid(form)

    def form_valid(self, form):
        # 로그인에 성공하면 실패 횟수를 지웁니다
        cache.delete(self._key())
        return super().form_valid(form)

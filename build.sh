#!/usr/bin/env bash
# 오류 발생 시 즉시 중단
set -o errexit

# 패키지 설치
pip install -r requirements.txt

# 정적 파일 모으기
python manage.py collectstatic --no-input

# 데이터베이스 마이그레이션
python manage.py migrate

# 초기 대표 레시피 데이터 적재
python manage.py seed_recipes
python manage.py shell -c "from recipes.models import Recipe; print(Recipe.objects.filter(title='고소한 알감자 조림').delete())"
# recipe_images 폴더의 사진을 레시피에 연결 (폴더가 없으면 건너뜀, 이미 사진 있는 레시피도 건너뜀)
python manage.py attach_images

# 관리자 계정 만들기: 환경변수 3개(USERNAME, EMAIL, PASSWORD)가 모두 있을 때만 (이미 있으면 무시)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py shell -c "import os; from django.contrib.auth import get_user_model; U=get_user_model(); u,_=U.objects.get_or_create(username=os.environ['DJANGO_SUPERUSER_USERNAME']); u.is_staff=True; u.is_superuser=True; u.set_password(os.environ['DJANGO_SUPERUSER_PASSWORD']); u.save(); print('superuser ready:', u.username)"
fi

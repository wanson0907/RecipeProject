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

# recipe_images 폴더의 사진을 레시피에 연결 (폴더가 없으면 건너뜀, 이미 사진 있는 레시피도 건너뜀)
python manage.py attach_images

# 관리자 계정 만들기: 환경변수 3개(USERNAME, EMAIL, PASSWORD)가 모두 있을 때만 (이미 있으면 무시)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
  python manage.py createsuperuser --noinput || true
fi

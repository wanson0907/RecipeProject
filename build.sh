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

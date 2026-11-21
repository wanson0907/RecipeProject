# 레시피 공유 사이트

## 처음 실행하기
```bash
pip install -r requirements.txt
python manage.py makemigrations recipes
python manage.py migrate
python manage.py createsuperuser   # 관리자 계정 (선택)
python manage.py runserver
```
브라우저에서 http://127.0.0.1:8000 접속

## 구조
- `config/` 프로젝트 설정 (settings.py, urls.py)
- `recipes/` 레시피 앱 (models.py = DB, views.py = 로직, forms.py = 입력폼, urls.py = 주소)
- `templates/` HTML (base.html을 모든 페이지가 상속)
- `static/css/style.css` 직접 만든 CSS

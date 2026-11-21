# 🍳 레시피 공유 및 AI 음식 추천 웹사이트 (RecipeSite)

> 사용자들이 서로의 요리 레시피를 공유하고, Google Gemini AI 셰프 챗봇을 통해 보유한 재료나 상황에 맞는 요리를 실시간으로 추천받을 수 있는 Django 기반 풀스택 웹 서비스입니다.

---

## ✨ 주요 기능
- **레시피 공유 & 탐색**: 레시피 등록/수정/삭제, 재료 및 만드는 법 단계별 안내, 검색 및 인기순 정렬
- **소통 기능**: 댓글 작성/삭제 및 레시피 '좋아요' 토글
- **🧑‍🍳 AI 맛비서 셰프 (Google Gemini API 연동)**:
  - 우측 하단 플로팅 챗봇을 통해 자연어 대화 지원 ("냉장고에 김치랑 돼지고기 있어", "15분 초간단 요리 알려줘")
  - 사이트 데이터베이스에 등록된 실제 레시피와 자동 매칭하여 링크 카드 추천
- **대량 레시피 시딩 & CSV 임포트**:
  - `python manage.py seed_recipes` (한국인 인기 대표 요리 20여 종 즉시 적재)
  - `python manage.py import_recipes_csv <파일명.csv>` (엑셀 CSV 일괄 업로드)

---

## 🚀 로컬 실행 방법 (Local Setup)

```bash
# 1. 필수 패키지 설치
pip install -r requirements.txt

# 2. .env 파일 생성 후 Gemini API 키 설정 (.env.example 참고)
# GEMINI_API_KEY=your_key_here

# 3. 데이터베이스 마이그레이션 & 초기 레시피 데이터 적재
python manage.py migrate
python manage.py seed_recipes

# 4. 개발 서버 실행
python manage.py runserver
```

---

## 🌐 Render.com 무료 클라우드 배포 가이드

1. **GitHub에 코드 푸시**
2. [render.com](https://render.com/)에서 **New +** ➡️ **Web Service** 선택 후 깃허브 저장소 연결
3. 설정 입력:
   - **Build Command**: `./build.sh` (또는 `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python manage.py seed_recipes`)
   - **Start Command**: `gunicorn config.wsgi:application`
   - **Environment Variables**:
     - `GEMINI_API_KEY`: 구글 Gemini API 키
     - `DJANGO_SECRET_KEY`: 임의의 긴 보안 문자열
     - `DEBUG`: `False`
4. **Create Web Service** 클릭 시 2~3분 내 무료 라이브 웹사이트 완성!

import json
import re
import requests
from django.conf import settings
from .models import Recipe


def get_recipe_context(limit=30):
    """
    DB에 등록된 레시피 목록을 AI가 이해할 수 있는 텍스트로 요약합니다.
    """
    recipes = Recipe.objects.all().order_by("-created_at")[:limit]
    if not recipes.exists():
        return "현재 사이트에 등록된 레시피가 없습니다."

    lines = []
    for r in recipes:
        ingredients_sample = ", ".join(r.ingredient_list()[:6])
        lines.append(
            f"- [ID: {r.id}] 제목: {r.title} | 한 줄 소개: {r.description or '없음'} | 주요 재료: {ingredients_sample}"
        )
    return "\n".join(lines)


def parse_recommended_ids(text):
    """
    AI 답변 텍스트에서 [RECOMMENDED_IDS: 1, 2, ...] 형태를 찾아내고,
    해당 태그를 답변 본문에서 제거한 뒤 (clean_text, id_list)를 반환합니다.
    """
    pattern = r"\[RECOMMENDED_IDS:\s*([0-9,\s]*)\]"
    match = re.search(pattern, text)
    ids = []
    clean_text = text

    if match:
        raw_ids = match.group(1).strip()
        if raw_ids:
            for item in raw_ids.split(","):
                item = item.strip()
                if item.isdigit():
                    ids.append(int(item))
        clean_text = re.sub(pattern, "", text).strip()

    return clean_text, ids


def fallback_keyword_search(user_message):
    """
    API 키가 없거나 호출 실패 시 실행되는 대체 추천 로직 (키워드 매칭)
    """
    keywords = [k.strip() for k in re.split(r"[\s,]+", user_message) if len(k.strip()) >= 2]
    matched_recipes = []
    if keywords:
        for r in Recipe.objects.all():
            text_corpus = f"{r.title} {r.description} {r.ingredients}"
            if any(k in text_corpus for k in keywords):
                matched_recipes.append(r)

    if not matched_recipes:
        matched_recipes = list(Recipe.objects.all()[:3])

    recommended_data = [
        {
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "image_url": r.image.url if r.image else "",
            "url": r.get_absolute_url(),
        }
        for r in matched_recipes[:3]
    ]
    return recommended_data


def ask_gemini_chef(user_message, history=None):
    """
    Google Gemini API를 호출하여 사용자에게 음식과 레시피를 추천합니다.
    """
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    model_name = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")

    # API 키가 설정되지 않은 경우 친절한 안내와 대체 추천 반환
    if not api_key:
        fallback_items = fallback_keyword_search(user_message)
        reply = (
            "안녕하세요! 맛있는 요리를 추천해 드리는 **맛비서 셰프**입니다. 🧑‍🍳\n\n"
            "현재 Google Gemini API 키(`GEMINI_API_KEY`)가 설정되지 않아 **기본 키워드 추천 모드**로 동작 중입니다.\n\n"
            "더 똑똑하고 자연스러운 AI 추천을 받으시려면 프로젝트의 `.env` 파일에 발급받으신 Gemini API 키를 입력해 주세요!\n\n"
            "입력해주신 내용과 어울릴 만한 사이트 레시피를 찾아보았어요. 아래 추천을 확인해 보세요!"
        )
        return {
            "reply": reply,
            "recipes": fallback_items,
            "is_fallback": True,
        }

    # 레시피 데이터베이스 컨텍스트 준비
    recipe_context = get_recipe_context()

    system_instruction = f"""
당신은 '레시피 공유' 사이트의 친절하고 센스 있는 전문 셰프 AI 챗봇 '맛비서'입니다.
사용자의 질문(보유 재료, 먹고 싶은 음식의 느낌/맛, 현재 상황, 날씨, 기분 등)을 세심하게 파악하여
가장 알맞은 음식과 요리법 팁을 친절하고 맛있게 설명해 주세요.

[우리 사이트의 등록 레시피 데이터]:
{recipe_context}

[답변 가이드라인]:
1. 말투는 다정하고 전문적이며 요리 열정이 넘치는 셰프 톤(해요체)으로 작성해 주세요. 이모티콘을 적절히 활용해 주세요.
2. 사용자의 상황이나 재료에 맞춰 사이트에 등록된 레시피가 있다면, 반드시 그 레시피를 우선적으로 추천하고 그 이유(맛의 조화, 조리 팁)를 함께 알려주세요.
3. 만약 사이트 등록 레시피 중에 딱 맞는 것이 없더라도, 일반적인 요리 아이디어나 맛있게 만들 수 있는 조리 팁을 친절하게 알려주세요.
4. 중요: 추천할 만한 우리 사이트 레시피가 있다면, 답변의 맨 마지막 줄에 반드시 아래 형식으로 해당 레시피의 ID 번호를 명시해 주세요. (없으면 적지 마세요)
   형식: [RECOMMENDED_IDS: 1, 3]
"""

    contents = []

    # 이전 대화 내역이 전달된 경우 추가 (최근 6개 내외)
    if history and isinstance(history, list):
        for msg in history[-6:]:
            role = "user" if msg.get("sender") == "user" else "model"
            text = msg.get("text", "").strip()
            if text:
                contents.append({"role": role, "parts": [{"text": text}]})

    # 현재 질문 추가
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    endpoint_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.95,
            "maxOutputTokens": 1000,
        },
    }

    try:
        response = requests.post(
            endpoint_url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=20,
        )

        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                raw_text = "".join(part.get("text", "") for part in parts)
                clean_text, recipe_ids = parse_recommended_ids(raw_text)

                # 추천된 레시피 객체 가져오기
                recommended_recipes = []
                if recipe_ids:
                    recipes_qs = Recipe.objects.filter(id__in=recipe_ids)
                    # ID 순서 유지
                    recipe_map = {r.id: r for r in recipes_qs}
                    for rid in recipe_ids:
                        if rid in recipe_map:
                            r = recipe_map[rid]
                            recommended_recipes.append(
                                {
                                    "id": r.id,
                                    "title": r.title,
                                    "description": r.description,
                                    "image_url": r.image.url if r.image else "",
                                    "url": r.get_absolute_url(),
                                }
                            )

                return {
                    "reply": clean_text,
                    "recipes": recommended_recipes,
                    "is_fallback": False,
                }
            else:
                return {
                    "reply": "죄송해요, 답변을 생성하지 못했습니다. 다시 한 번 질문해 주시겠어요?",
                    "recipes": [],
                    "is_fallback": False,
                }

        else:
            error_data = response.json().get("error", {})
            error_msg = error_data.get("message", response.text)
            fallback_items = fallback_keyword_search(user_message)
            return {
                "reply": f"Gemini API 호출 중 문제가 발생했습니다: {error_msg}\n\n대신 사이트의 추천 레시피를 확인해 보세요!",
                "recipes": fallback_items,
                "is_fallback": True,
            }

    except requests.exceptions.RequestException as e:
        fallback_items = fallback_keyword_search(user_message)
        return {
            "reply": f"AI 서버와 통신 중 연결 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.\n(오류 내용: {str(e)})",
            "recipes": fallback_items,
            "is_fallback": True,
        }

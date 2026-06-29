import os
import json
from google import genai
from google.genai import types

def dig_music_with_gemini(user_prompt):
    """
    유저의 입력을 받아 Gemini가 곡 정보, 장르, 실제 가사를 정형화된 JSON으로 반환합니다.
    """
    try:
        # 환경 변수 혹은 주입된 시스템 키로부터 Gemini 클라이언트 초기화
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    except Exception as e:
        print(f"Gemini 클라이언트 초기화 실패: {e}")
        return None

    prompt_instruction = f"""
    당신은 전세계의 모든 음악 장르와 히스토리를 꿰뚫고 있는 음악 디깅 AI 에이전트입니다.
    유저가 원하는 무드, 상황, 장르를 말하면 그에 완벽히 부합하는 '실제 존재하는 명곡 1곡'과 '연관 추천곡 3곡'을 추천해야 합니다.
    
    유저의 요청 무드/내용: {user_prompt}
    
    반드시 다음 Key값을 가진 순수한 JSON 구조로만 답변하세요. 
    텍스트 앞뒤에 소스코드 블록 기호(```json 또는 ```)를 절대 붙이지 말고 오직 순수 JSON 문자열만 반환하세요:
    {{
        "title": "정확한 곡 제목 (피처링 정보 제외)",
        "artist": "가수 이름 (피처링 정보 제외)",
        "featuring": "피처링 참여 가수가 있다면 기입 (없다면 '없음')",
        "year": "실제 발매 년도 (예: 2022년)",
        "genre": "디깅된 정밀 세부 장르 이름 (예: Neo-Soul, City Pop, Lofi Chill)",
        "lyrics": ["1마디 실제 가사", "2마디 실제 가사", "3마디 실제 가사", "4마디 실제 가사", "5마디 실제 가사", "6마디 실제 가사"],
        "search_keyword": "유튜브에서 해당 음악의 고화질 음원/영상을 찾기 위한 가장 정확한 키워드 (예: 뉴진스 Ditto 오피셜)",
        "playlist_keywords": ["연관 추천 곡 검색 키워드 1", "연관 추천 곡 검색 키워드 2", "연관 추천 곡 검색 키워드 3"]
    }}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_instruction,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Gemini 디깅 실행 에러: {e}")
        return None

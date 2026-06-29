import os
import streamlit as st
from dotenv import load_dotenv
from googleapiclient.discovery import build

# 에이전트 파일로부터 함수 가져오기
from agent import dig_music_with_gemini

load_dotenv()

# 1. 페이지 레이아웃 설정 (넓은 화면을 활용하기 위해 'wide'로 설정)
st.set_page_config(page_title="Music Digging AI Agent", page_icon="🎧", layout="wide")

# CSS를 활용해 스크롤 없이 한눈에 들어오도록 컴팩트화
st.markdown("""
    <style>
    /* 상하 여백을 최소화하여 한 화면에 다 담기도록 조절 */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
    }
    /* 음악 정보 카드 컴팩트 디자인 */
    .music-card {
        background-color: #f0f2f6;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
        color: #111111;
        font-size: 14px;
    }
    /* 가사 박스 높이를 줄여 한눈에 보이게 고정 */
    .lyrics-scroll-box {
        background-color: #111111;
        color: #ffffff;
        padding: 12px;
        border-radius: 8px;
        font-family: 'Malgun Gothic', sans-serif;
        max-height: 110px;
        overflow-y: auto;
        text-align: center;
        line-height: 1.6em;
        font-size: 13px;
        border: 1px solid #333;
    }
    /* 대화창 영역 스크롤 고정 및 높이 확보 */
    .chat-container {
        max-height: 520px;
        overflow-y: auto;
        padding-right: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎵 Music Digging Agent Hub")

# 세션 상태(Session State) 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 어떤 분위기나 장르의 음악 세계를 깊이 파고들어 볼까요?"}]
if "current_track" not in st.session_state:
    st.session_state.current_track = None

# 유튜브 Data API v3를 사용한 영상 검색 헬퍼 함수
def get_youtube_video_via_api(keyword):
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return None
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        search_response = youtube.search().list(
            q=keyword,
            part="id,snippet",
            maxResults=1,
            type="video",
            videoCategoryId="10"
        ).execute()
        
        items = search_response.get("items", [])
        if items:
            v_id = items[0]["id"]["videoId"]
            return {
                "id": v_id,
                "title": items[0]["snippet"]["title"],
                "channel": items[0]["snippet"]["channelTitle"],
                "thumbnail": f"https://i.ytimg.com/vi/{v_id}/maxresdefault.jpg"
            }
    except Exception as e:
        print(f"유튜브 API 호출 에러: {e}")
    return None

# =========================================================
# 🏛️ 레이아웃 좌우 분할 (좌측: 음악 플레이어 허브 / 우측: AI 대화창)
# =========================================================
left_col, right_col = st.columns([1, 1])  # 5:5 비율로 균형 있게 분할

# --- 1. 좌측 영역: 음악 및 UI (스크롤 없이 한눈에 보기) ---
with left_col:
    st.subheader("🎧 Now Playing Hub")
    track = st.session_state.current_track
    
    if track:
        # 앨범아트와 곡 메타데이터를 컴팩트하게 가로 배정
        meta_col1, meta_col2 = st.columns([2, 3])
        with meta_col1:
            st.image(track["album_art"], use_container_width=True)
        with meta_col2:
            st.markdown(f"""
                <div class="music-card">
                    <h4 style='margin-top:0px; margin-bottom:4px; color:#FF4B4B;'>🎵 {track['title']}</h4>
                    <p style='margin:2px 0;'><b>🎤</b> {track['artist']}</p>
                    <p style='margin:2px 0;'><b>📅</b> {track['year']}</p>
                    <p style='margin:2px 0;'><b>🏷️</b> {track['genre']}</p>
                </div>
            """, unsafe_allow_html=True)
        
        # 유튜브 미디어 플레이어 (크기 자동 최적화)
        st.video(f"https://www.youtube.com/watch?v={track['youtube_id']}")
        
        # 정적 가사 뷰어 (컴팩트 스크롤 박스)
        lyrics_html = "".join([f"<p style='margin:2px 0;'>{line}</p>" for line in track["lyrics"]])
        st.markdown(f"<div class='lyrics-scroll-box'>{lyrics_html}</div>", unsafe_allow_html=True)
        
        # 연관 추천곡 접이식 메뉴 (기본 닫힘 상태로 공간 절약)
        with st.expander("🗂️ 추천 리스트 및 YouTube 플레이리스트 담기", expanded=False):
            for p_song in track["playlist"]:
                st.markdown(f"▶️ [{p_song['title']}]({f'https://www.youtube.com/watch?v={p_song['id']}'}) - {p_song['artist']}")
            
            all_ids = [track["youtube_id"]] + [p["id"] for p in track["playlist"]]
            export_url = f"https://www.youtube.com/watch_videos?video_ids={','.join(all_ids)}"
            st.link_button("🚀 YouTube 재생목록에 생성", export_url, use_container_width=True)
    else:
        st.info("💡 우측 대화창에 원하는 사운드 무드나 상황을 입력하시면, 이 자리에 스크롤이 필요 없는 컴팩트 음악 플레이어 허브가 생성됩니다.")

# --- 2. 우측 영역: Gemini AI 대화창 ---
with right_col:
    st.subheader("🤖 AI 에이전트 대화 창")
    
    # 대화 내용들을 스크롤 가능한 영역 안에 격리
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 챗 바 하단 고정
    if user_input := st.chat_input("원하는 무드, 가사 느낌, 혹은 장르를 입력하세요..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.rerun()

# --- 비동기 트리거 로직 처리 (화면 갱신 후 호출 데이터 매칭) ---
if st.session_state.messages[-1]["role"] == "user":
    user_input = st.session_state.messages[-1]["content"]
    
    with st.spinner("🧠 Gemini 디깅 분석 중..."):
        ai_data = dig_music_with_gemini(user_input)
        
    if ai_data:
        with st.spinner("🎬 매칭 미디어 트래킹 중..."):
            main_video = get_youtube_video_via_api(ai_data["search_keyword"])
            
            playlist_tracks = []
            if ai_data.get("playlist_keywords"):
                for kw in ai_data["playlist_keywords"]:
                    sub_v = get_youtube_video_via_api(kw)
                    if sub_v:
                        playlist_tracks.append({
                            "title": sub_v["title"],
                            "artist": sub_v["channel"],
                            "id": sub_v["id"]
                        })
            
            if main_video:
                feat_str = f" (Feat. {ai_data['featuring']})" if ai_data.get('featuring') and ai_data['featuring'] != '없음' else ""
                
                st.session_state.current_track = {
                    "title": ai_data["title"],
                    "artist": f"{ai_data['artist']}{feat_str}",
                    "year": ai_data["year"],
                    "genre": ai_data["genre"],
                    "youtube_id": main_video["id"],
                    "album_art": main_video["thumbnail"],
                    "lyrics": ai_data["lyrics"],
                    "playlist": playlist_tracks
                }
                
                reply = f"🤖 **[{ai_data['genre']}]** 무드의 명곡을 디깅했습니다! 좌측 음악 허브 창에서 한눈에 확인해 보세요."
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()
    else:
        st.error("디깅에 실패했습니다. 코드를 재확인해 주세요.")

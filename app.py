import os
import streamlit as st
from dotenv import load_dotenv
from googleapiclient.discovery import build

# 에이전트 파일로부터 함수 가져오기
from agent import dig_music_with_gemini

load_dotenv()

# 1. 페이지 레이아웃 설정 (넓은 화면 및 타이틀 최적화)
st.set_page_config(page_title="Music Digging AI Agent", page_icon="🎧", layout="wide")

# CSS를 활용해 전체 화면 스크롤을 완전히 없애고(고정) 좌우 독립 스크롤 구현
st.markdown("""
    <style>
    /* 1. 웹페이지 전체 화면 스크롤 제거 (가장 중요) */
    html, body, [data-testid="stAppViewContainer"] {
        overflow: hidden !important;
        height: 100vh !important;
    }
    
    /* 상단 기본 헤더/여백 타이트하게 조절 */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        max-height: 100vh !important;
    }
    
    /* 2. 좌측 음악 허브 전용 컨테이너 (스크롤 없이 고정되도록 유도) */
    .left-hub-box {
        max-height: 85vh;
        overflow-y: auto;
        padding-right: 5px;
    }
    
    /* 음악 정보 카드 컴팩트 디자인 */
    .music-card {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 8px;
        color: #111111;
        font-size: 13px;
    }
    
    /* 가사 박스 높이를 고정하여 스크롤 유도 */
    .lyrics-scroll-box {
        background-color: #111111;
        color: #ffffff;
        padding: 10px;
        border-radius: 6px;
        font-family: 'Malgun Gothic', sans-serif;
        max-height: 100px;
        overflow-y: auto;
        text-align: center;
        line-height: 1.5em;
        font-size: 12px;
        border: 1px solid #333;
    }
    
    /* 3. 우측 독립형 챗 UI 컨테이너 (대화창만 따로 스크롤) */
    .chat-scroll-area {
        height: 62vh;
        overflow-y: auto;
        border: 1px solid #eee;
        border-radius: 8px;
        padding: 10px;
        background-color: #fafafa;
        margin-bottom: 10px;
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
# 🏛️ 뷰포트 고정형 좌우 레이아웃 (5:5 비율 분할)
# =========================================================
left_col, right_col = st.columns([1, 1])

# --- 1. 좌측 영역: 음악 및 UI 허브 (전체 화면 스크롤 방지 래퍼 적용) ---
with left_col:
    st.markdown('<div class="left-hub-box">', unsafe_allow_html=True)
    st.subheader("🎧 Now Playing Hub")
    track = st.session_state.current_track
    
    if track:
        meta_col1, meta_col2 = st.columns([2, 3])
        with meta_col1:
            st.image(track["album_art"], use_container_width=True)
        with meta_col2:
            st.markdown(f"""
                <div class="music-card">
                    <h5 style='margin-top:0px; margin-bottom:4px; color:#FF4B4B;'>🎵 {track['title']}</h5>
                    <p style='margin:1px 0;'><b>🎤</b> {track['artist']}</p>
                    <p style='margin:1px 0;'><b>📅</b> {track['year']}</p>
                    <p style='margin:1px 0;'><b>🏷️</b> {track['genre']}</p>
                </div>
            """, unsafe_allow_html=True)
        
        # 미디어 플레이어 크기 고정 배치
        st.video(f"https://www.youtube.com/watch?v={track['youtube_id']}")
        
        # 가사 뷰어
        lyrics_html = "".join([f"<p style='margin:2px 0;'>{line}</p>" for line in track["lyrics"]])
        st.markdown(f"<div class='lyrics-scroll-box'>{lyrics_html}</div>", unsafe_allow_html=True)
        
        # 추천곡 접이식 레이아웃
        with st.expander("🗂️ 추천 리스트 및 단축키", expanded=False):
            for p_song in track["playlist"]:
                st.markdown(f"▶️ [{p_song['title']}]({f'https://www.youtube.com/watch?v={p_song['id']}'}) - {p_song['artist']}")
            
            all_ids = [track["youtube_id"]] + [p["id"] for p in track["playlist"]]
            export_url = f"https://www.youtube.com/watch_videos?video_ids={','.join(all_ids)}"
            st.link_button("🚀 YouTube 재생목록 연동 생성", export_url, use_container_width=True)
    else:
        st.info("💡 우측 챗봇에게 음악 무드나 상황을 던져보세요! 이 자리에 한눈에 들어오는 컴팩트 음악 재생 허브가 박히게 됩니다.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 2. 우측 영역: Gemini 독립형 챗 UI (대화창만 따로 스크롤) ---
with right_col:
    st.subheader("💬 Gemini Music Digging Agent")
    
    # 별도 스크롤 박스로 대화 내용들만 가둠
    st.markdown('<div class="chat-scroll-area">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 유저 대화창 입력란을 하단에 단독 배치
    if user_input := st.chat_input("원하는 무드, 가사 느낌, 혹은 장르를 입력하세요..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.rerun()

# --- 비동기 백엔드 오케스트레이션 로직 ---
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
                
                reply = f"🤖 **[{ai_data['genre']}]** 무드의 음악을 아카이빙했습니다! 왼쪽 대시보드 허브에서 재생해 보세요."
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()
    else:
        st.error("디깅에 실패했습니다. 코드를 재확인해 주세요.")

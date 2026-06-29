import os
import streamlit as st
from dotenv import load_dotenv
from googleapiclient.discovery import build

# 에이전트 파일로부터 함수 가져오기
from agent import dig_music_with_gemini

load_dotenv()

# 1. 페이지 레이아웃 설정
st.set_page_config(page_title="Music Digging AI Agent", page_icon="🎧", layout="wide")

# CSS를 활용해 전체 화면 고정 및 스마트폰 형태의 카카오톡 스타일 챗 UI 구현
st.markdown("""
    <style>
    /* 웹페이지 전체 화면 스크롤 제거 */
    html, body, [data-testid="stAppViewContainer"] {
        overflow: hidden !important;
        height: 100vh !important;
        background-color: #f5f6f7;
    }
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 0rem !important;
        max-height: 100vh !important;
    }
    
    /* 좌측 음악 허브 전용 컨테이너 */
    .left-hub-box {
        max-height: 85vh;
        overflow-y: auto;
        padding-right: 10px;
    }
    
    .music-card {
        background-color: #ffffff;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 8px;
        color: #111111;
        font-size: 13px;
        border: 1px solid #e1e4e6;
    }
    
    .lyrics-scroll-box {
        background-color: #000000;
        color: #00ffcc; /* 가사 네온 민트 컬러 */
        padding: 15px;
        border-radius: 8px;
        font-family: 'Malgun Gothic', sans-serif;
        max-height: 220px; /* 🎚️ 기존 110px에서 220px로 확장하여 더 많은 가사가 한눈에 보이도록 변경 */
        overflow-y: auto;
        text-align: center;
        line-height: 1.8em;
        font-size: 13px;
        border: 1px solid #30363d;
    }
    
    /* 🔥 카카오톡/스마트폰 스크린 스타일의 우측 챗 프레임 박스 */
    .phone-chat-box {
        border: 2px solid #dcdfe2;
        border-radius: 24px; /* 꼭짓점이 대폭 둥근 사각형 연출 */
        padding: 18px;
        background-color: #bacee0; /* 카카오톡 기본 대화방 느낌의 파스텔 블루 배경 */
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        height: 74vh;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    /* 챗 박스 내부의 독립형 대화 스크롤 영역 */
    .chat-scroll-inside {
        height: 100%;
        overflow-y: auto;
        padding-right: 5px;
        margin-bottom: 10px;
    }
    
    /* 스크롤바 디자인 커스텀 (깔끔하게 구현) */
    ::-webkit-scrollbar {
        width: 5px;
    }
    ::-webkit-scrollbar-thumb {
        background: #bcc0c4;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎵 Music Digging Agent Hub")

# 세션 상태(Session State) 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 어떤 분위기나 장르의 음악 세계를 깊이 파고들어 볼까요?"}]
if "current_track" not in st.session_state:
    st.session_state.current_track = None

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
# 🏛️ 레이아웃 좌우 분할 (좌측: 음악 플레이어 허브 / 우측: 카톡 폰 스타일 챗 UI)
# =========================================================
left_col, right_col = st.columns([1, 1])

# --- 1. 좌측 영역: 음악 및 UI 허브 ---
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
        
        st.video(f"https://www.youtube.com/watch?v={track['youtube_id']}")
        
        lyrics_html = "".join([f"<p style='margin:2px 0;'>{line}</p>" for line in track["lyrics"]])
        st.markdown(f"<div class='lyrics-scroll-box'>{lyrics_html}</div>", unsafe_allow_html=True)
        
        with st.expander("🗂️ 추천 리스트 및 단축키", expanded=False):
            for p_song in track["playlist"]:
                st.markdown(f"▶️ [{p_song['title']}]({f'https://www.youtube.com/watch?v={p_song['id']}'}) - {p_song['artist']}")
            
            all_ids = [track["youtube_id"]] + [p["id"] for p in track["playlist"]]
            export_url = f"https://www.youtube.com/watch_videos?video_ids={','.join(all_ids)}"
            st.link_button("🚀 YouTube 재생목록 연동 생성", export_url, use_container_width=True)
    else:
        st.info("💡 우측 메신저에 음악 무드나 상황을 메시지로 톡 보내보세요! 이 자리에 컴팩트 음악 재생 대시보드가 생성됩니다.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 2. 우측 영역: 핸드폰 카카오톡 스타일 테두리 챗 UI ---
with right_col:
    st.subheader("💬 Gemini Messenger")
    
    # 둥근 모서리 스마트폰 모양 묶음 박스 시작
    st.markdown('<div class="phone-chat-box">', unsafe_allow_html=True)
    
    # 내부 대화 전용 스크롤 레이어
    st.markdown('<div class="chat-scroll-inside">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    st.markdown('</div>', unsafe_allow_html=True) # 내부 대화창 닫기
    
    # 박스 내 하단에 자연스럽게 자리 잡도록 유저 대화창 입력란을 여기에 배치
    if user_input := st.chat_input("에이전트에게 톡 보내기..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True) # 스마트폰 메인 프레임 박스 닫기

# --- 비동기 백엔드 오케스트레이션 로직 ---
if st.session_state.messages[-1]["role"] == "user":
    user_input = st.session_state.messages[-1]["content"]
    
    with st.spinner("🧠 톡 확인 후 디깅 분석 중..."):
        ai_data = dig_music_with_gemini(user_input)
        
    if ai_data:
        with st.spinner("🎬 음악 영상 매칭 중..."):
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
                
                reply = f"🤖 **[{ai_data['genre']}]** 무드의 노래를 보냈습니다! 왼쪽 재생 허브를 터치해 확인해 보세요."
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()
    else:
        st.error("디깅에 실패했습니다. 코드를 재확인해 주세요.")

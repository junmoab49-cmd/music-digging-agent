import os
import streamlit as st
from dotenv import load_dotenv
from googleapiclient.discovery import build

# 에이전트 파일로부터 함수 가져오기 (이 부분의 들여쓰기를 완벽히 제거했습니다)
from agent import dig_music_with_gemini

load_dotenv()

# 1. 페이지 레이아웃 설정
st.set_page_config(page_title="Music Digging AI Agent", page_icon="🎧", layout="wide")

# CSS를 활용해 전체 화면 고정 및 눈이 편안한 다크 모드 구현
st.markdown("""
    <style>
    /* 웹페이지 전체 화면 스크롤 제거 */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0d1117 !important;
        color: #ecf0f1 !important;
        overflow: hidden !important;
        height: 100vh !important;
    }
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 0rem !important;
        max-height: 100vh !important;
    }
    
    h1 {
        color: #ffffff !important;
    }
    
    /* 좌측 음악 허브 전용 컨테이너 */
    .left-hub-box {
        max-height: 85vh;
        overflow-y: auto;
        padding: 15px;
        background-color: #070a0f;
        border-radius: 16px;
        border: 1px solid #1f2937;
    }
    
    .music-card {
        background-color: #161b22;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 8px;
        color: #ffffff !important;
        border: 1px solid #30363d;
    }
    
    .lyrics-scroll-box {
        background-color: #000000;
        color: #00ffcc;
        padding: 15px;
        border-radius: 8px;
        font-family: 'Malgun Gothic', sans-serif;
        max-height: 220px;
        overflow-y: auto;
        text-align: center;
        line-height: 1.8em;
        font-size: 13px;
        border: 1px solid #30363d;
    }
    
    /* 우측 채팅 허브 디자인 */
    .phone-chat-box {
        border: 2px solid #30363d;
        border-radius: 24px;
        padding: 18px;
        background-color: #1f232b;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        height: 74vh;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .chat-scroll-inside {
        height: 100%;
        overflow-y: auto;
        padding-right: 5px;
        margin-bottom: 10px;
    }
    
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-thumb {
        background: #30363d;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #484f58;
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

# 레이아웃 좌우 분할
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
                    <h5 style='margin-top:0px; margin-bottom:4px; color:#ff4757;'>🎵 {track['title']}</h5>
                    <p style='margin:1px 0; color:#b3b9c1;'><b>🎤</b> {track['artist']}</p>
                    <p style='margin:1px 0; color:#b3b9c1;'><b>📅</b> {track['year']}</p>
                    <p style='margin:1px 0; color:#b3b9c1;'><b>🏷️</b> {track['genre']}</p>
                </div>
            """, unsafe_allow_html=True)
        
        st.video(f"https://www.youtube.com/watch?v={track['youtube_id']}")
        
        lyrics_html = "".join([f"<p style='margin:2px 0;'>{line}</p>" for line in track["lyrics"]])
        st.markdown(f"<div class='lyrics-scroll-box'>{lyrics_html}</div>", unsafe_allow_html=True)
        
        with st.expander("🗂️ 추천 리스트 및 연동", expanded=False):
            for p_song in track["playlist"]:
                st.markdown(f"▶️ [{p_song['title']}]({f'https://www.youtube.com/watch?v={p_song['id']}'}) - {p_song['artist']}")
            
            all_ids = [track["youtube_id"]] + [p["id"] for p in track["playlist"]]
            export_url = f"https://www.youtube.com/watch_videos?video_ids={','.join(all_ids)}"
            st.link_button("🚀 YouTube 재생목록 연동 생성", export_url, use_container_width=True)
    else:
        st.info("💡 우측 메신저에 음악 무드나 장르를 톡으로 보내보세요! 좌측 딥 다크 허브에 음악 플레이어가 나타납니다.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 2. 우측 영역: 카카오톡 다크모드 스타일 UI ---
with right_col:
    st.subheader("💬 Gemini Messenger")
    
    st.markdown('<div class="phone-chat-box">', unsafe_allow_html=True)
    
    st.markdown('<div class="chat-scroll-inside">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    if user_input := st.chat_input("에이전트에게 톡 보내기..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)

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
                
                reply = f"🤖 **[{ai_data['genre']}]** 무드의 음악을 전송했습니다. 왼쪽 재생 허브를 확인해 보세요!"
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()
    else:
        st.error("디깅에 실패했습니다. 코드를 재확인해 주세요.")

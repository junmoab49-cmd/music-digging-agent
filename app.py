import os
import streamlit as st
from dotenv import load_dotenv
from googleapiclient.discovery import build
from agent import dig_music_with_gemini

load_dotenv()

# 페이지 설정
st.set_page_config(page_title="Music Digging AI Agent", page_icon="🎧", layout="wide")

# CSS: 복잡한 윈도우 고정 로직을 빼고, 순수하게 색상 대비와 카카오톡 둥근 박스 껍데기만 남겨 렌더링 버그를 차단합니다.
st.markdown("""
    <style>
    /* 전체 배경 다크 테마 */
    .stApp {
        background-color: #0d1117 !important;
        color: #ecf0f1 !important;
    }
    
    /* 좌측 음악 허브 박스 (딥 블랙) */
    .left-hub-box {
        padding: 20px;
        background-color: #070a0f;
        border-radius: 16px;
        border: 1px solid #1f2937;
        margin-bottom: 20px;
    }
    
    /* 음악 카드 */
    .music-card {
        background-color: #161b22;
        padding: 15px;
        border-radius: 12px;
        color: #ffffff !important;
        border: 1px solid #30363d;
    }
    
    /* 가사 스크롤 상자 */
    .lyrics-scroll-box {
        background-color: #000000;
        color: #00ffcc;
        padding: 15px;
        border-radius: 8px;
        font-family: 'Malgun Gothic', sans-serif;
        height: 250px;
        overflow-y: auto;
        text-align: center;
        line-height: 1.8em;
        font-size: 13px;
        border: 1px solid #30363d;
        margin-top: 10px;
    }
    
    /* 🔥 우측 카카오톡 스타일 스마트폰 둥근 테두리 박스 */
    .phone-chat-box {
        border: 2px solid #30363d;
        border-radius: 28px; /* 세로가 길고 꼭짓점이 둥근 형태 강조 */
        padding: 20px;
        background-color: #1f232b; /* 확실한 색상 차이 분리 */
        box-shadow: 0 6px 24px rgba(0,0,0,0.4);
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎵 Music Digging Agent Hub")

# 세션 상태 초기화
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
            q=keyword, part="id,snippet", maxResults=1, type="video", videoCategoryId="10"
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
        print(f"유튜브 에러: {e}")
    return None

# 좌우 레이아웃 분할
left_col, right_col = st.columns([1, 1])

# --- [좌측 레고 블록: 음악 재생 허브] ---
with left_col:
    st.markdown('<div class="left-hub-box">', unsafe_allow_html=True)
    st.subheader("🎧 Now Playing Hub")
    track = st.session_state.current_track
    
    if track:
        m1, m2 = st.columns([2, 3])
        with m1:
            st.image(track["album_art"], use_container_width=True)
        with m2:
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
            for p in track["playlist"]:
                st.markdown(f"▶️ [{p['title']}](https://www.youtube.com/watch?v={p['id']}) - {p['artist']}")
            all_ids = [track["youtube_id"]] + [p["id"] for p in track["playlist"]]
            st.link_button("🚀 YouTube 재생목록 연동", f"https://www.youtube.com/watch_videos?video_ids={','.join(all_ids)}", use_container_width=True)
    else:
        st.info("💡 우측 메신저에 음악 무드나 장르를 톡으로 보내보세요! 좌측 딥 다크 허브에 음악 플레이어와 전체 가사가 나타납니다.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- [우측 레고 블록: 카카오톡 스타일 메신저 팩] ---
with right_col:
    st.subheader("💬 Gemini Messenger")
    
    # 카카오톡 스마트폰 외형 컨테이너 시작
    st.markdown('<div class="phone-chat-box">', unsafe_allow_html=True)
    
    # 대화 기록 렌더링
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    st.markdown('</div>', unsafe_allow_html=True) # 컨테이너 마감
    
    # 입력창과 백엔드 오케스트레이션을 완벽하게 병합해 무한 루프 원천 차단
    if user_input := st.chat_input("에이전트에게 톡 보내기..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.spinner("🧠 톡 확인 후 음악 디깅 분석 중..."):
            ai_data = dig_music_with_gemini(user_input)
            
        if ai_data:
            main_video = get_youtube_video_via_api(ai_data["search_keyword"])
            playlist_tracks = []
            if ai_data.get("playlist_keywords"):
                for kw in ai_data["playlist_keywords"]:
                    sub_v = get_youtube_video_via_api(kw)
                    if sub_v:
                        playlist_tracks.append({"title": sub_v["title"], "artist": sub_v["channel"], "id": sub_v["id"]})
            
            if main_video:
                feat_str = f" (Feat. {ai_data['featuring']})" if ai_data.get('featuring') and ai_data['featuring'] != '없음' else ""
                st.session_state.current_track = {
                    "title": ai_data["title"], "artist": f"{ai_data['artist']}{feat_str}", "year": ai_data["year"], "genre": ai_data["genre"],
                    "youtube_id": main_video["id"], "album_art": main_video["thumbnail"], "lyrics": ai_data["lyrics"], "playlist": playlist_tracks
                }
                reply = f"🤖 **[{ai_data['genre']}]** 무드의 음악을 톡으로 전송했습니다. 왼쪽 재생 허브를 터치해 보세요!"
                st.session_state.messages.append({"role": "assistant", "content": reply})
        else:
            st.error("디깅 도중 오류가 발생했습니다.")
            
        st.rerun()

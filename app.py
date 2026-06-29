import os
import streamlit as st
from dotenv import load_dotenv
from googleapiclient.discovery import build

# 에이전트 파일로부터 함수 가져오기
from agent import dig_music_with_gemini

load_dotenv()

# 1. 페이지 레이아웃 설정 (중앙 집중형을 위해 레이아웃을 'centered'로 변경)
st.set_page_config(page_title="Music Digging AI Agent", page_icon="🎧", layout="centered")

# CSS를 활용해 레이아웃 컴팩트화 및 가사 뷰어 고도화
st.markdown("""
    <style>
    /* 여백 줄여서 한눈에 들어오게 조절 */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    .music-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        color: #111111;
    }
    .lyrics-scroll-box {
        background-color: #111111;
        color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        font-family: 'Malgun Gothic', sans-serif;
        max-height: 140px;
        overflow-y: auto;
        text-align: center;
        line-height: 1.8em;
        font-size: 14px;
        border: 1px solid #333;
    }
    .chat-box {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        background-color: #ffffff;
        max-height: 300px;
        overflow-y: auto;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎧 Music Digging Agent Hub")

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

# ==========================================
# 🏛️ 레이아웃 1층: NOW PLAYING (화면 중앙 상단)
# ==========================================
track = st.session_state.current_track

if track:
    # 앨범아트와 곡 메타데이터를 나란히 배치해 공간 절약
    meta_col1, meta_col2 = st.columns([1, 2])
    with meta_col1:
        st.image(track["album_art"], use_container_width=True)
    with meta_col2:
        st.markdown(f"""
            <div class="music-card">
                <h3 style='margin-top:0px; margin-bottom:5px; color:#FF4B4B;'>🎵 {track['title']}</h3>
                <p style='margin:2px 0;'><b>🎤 아티스트</b>: {track['artist']}</p>
                <p style='margin:2px 0;'><b>📅 발매년도</b>: {track['year']}</p>
                <p style='margin:2px 0;'><b>🏷️ 장르</b>: {track['genre']}</p>
            </div>
        """, unsafe_allow_html=True)
    
    # 음악 재생 플레이어
    st.video(f"https://www.youtube.com/watch?v={track['youtube_id']}")
    
    # 전체 가사 스크롤 박스 (싱크 어긋남 방지형 정적 뷰)
    st.markdown("##### 🎙️ Digging Lyrics")
    lyrics_html = "".join([f"<p style='margin:4px 0;'>{line}</p>" for line in track["lyrics"]])
    st.markdown(f"<div class='lyrics-scroll-box'>{lyrics_html}</div>", unsafe_allow_html=True)
    
    # 추천곡 및 내보내기 버튼 컴팩트화
    with st.expander("🗂️ 연관 디깅 리스트 및 YouTube 담기"):
        for p_song in track["playlist"]:
            st.markdown(f"▶️ [{p_song['title']}]({f'https://www.youtube.com/watch?v={p_song['id']}'}) - {p_song['artist']}")
        
        all_ids = [track["youtube_id"]] + [p["id"] for p in track["playlist"]]
        export_url = f"https://www.youtube.com/watch_videos?video_ids={','.join(all_ids)}"
        st.link_button("🚀 발견한 플레이리스트 내 YouTube 재생목록에 담기", export_url, use_container_width=True)
else:
    st.info("하단 대화창에 원하는 분위기, 장르, 상황을 입력하시면 여기에 음악 Hub가 활성화됩니다.")

st.divider()

# ==========================================
# 🏛️ 레이아웃 2층: AI 대화창 (화면 중앙 하단)
# ==========================================
st.subheader("🤖 AI 에이전트 대화")

# 스크롤 가능한 대화 박스 형태 구현
with st.container():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 유저 입력창 처리 로직
if user_input := st.chat_input("원하는 무드, 가사 느낌, 혹은 장르를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    
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
                
                reply = f"🤖 **[{ai_data['genre']}]** 세계관에서 곡을 발굴했습니다! 상단 재생 허브에서 가사와 함께 감상해 보세요."
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()
    else:
        st.error("디깅에 실패했습니다. 코드를 재확인해 주세요.")

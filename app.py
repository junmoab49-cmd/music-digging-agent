import os
import time
import streamlit as st
from dotenv import load_dotenv
from googleapiclient.discovery import build

# 에이전트 파일로부터 함수 가져오기
from agent import dig_music_with_gemini

load_dotenv()

# 1. 페이지 레이아웃 설정
st.set_page_config(page_title="Music Digging AI Agent", page_icon="🎧", layout="wide")

# CSS를 활용한 디자인 커스텀
st.markdown("""
    <style>
    .music-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        color: #111111;
    }
    .lyrics-box {
        background-color: #111111;
        color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        font-family: 'Malgun Gothic', sans-serif;
        height: 180px;
        overflow-y: auto;
        text-align: center;
        line-height: 2em;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎵 개인의 성장을 도우며 취향을 찾는 Music Digging Agent")
st.caption("Gemini 인텔리전스 기반 맞춤 장르 음악 아카이빙 및 가사 동기화 아키텍처")

# 사이드바: 가상 유튜브 연동 기능 및 검색 엔진 세팅
with st.sidebar:
    st.header("🔐 내 YouTube 계정 연동")
    yt_channel_id = st.text_input("YouTube 채널 ID 또는 이메일 입력", placeholder="UCxxxxxxxxxxxx")
    
    if yt_channel_id:
        st.success("✅ YouTube 계정이 가상 연동되었습니다!")
        st.info("디깅한 리스트를 내 유튜브 플레이리스트 묶음으로 전송할 준비가 되었습니다.")
    else:
        st.warning("계정을 입력하시면 맞춤형 플레이리스트 연동 기능이 활성화됩니다.")

# 세션 상태(Session State) 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 어떤 분위기나 장르의 음악 세계를 깊이 파고들어 볼까요? 상황이나 무드를 편하게 말씀해 주세요."}]
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
            videoCategoryId="10"  # 음악(Music) 카테고리만 필터링
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

# 메인 레이아웃 분할 (좌측: 챗봇 대화창 / 우측: 음악 재생 플레이어 및 라이브 가사)
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("🤖 AI 에이전트와 디깅 대화")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("원하는 무드, 가사 느낌, 혹은 장르를 입력하세요..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.spinner("🧠 Gemini가 음악 데이터베이스를 디깅 중..."):
            ai_data = dig_music_with_gemini(user_input)
            
        if ai_data:
            with st.spinner("🎬 YouTube에서 일치하는 고화질 영상을 매칭하는 중..."):
                main_video = get_youtube_video_via_api(ai_data["search_keyword"])
                
                # 연관 추천 트랙 3곡 검색 및 빌드
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
                    
                    reply = f"🤖 당신만을 위한 장르 **[{ai_data['genre']}]** 세계관에서 곡을 발굴했습니다!\n\n**{ai_data['artist']}**의 *{ai_data['title']}*{feat_str} 입니다. 우측 시스템 허브에서 실시간 싱크 마디 가사와 미디어를 확인해 보세요."
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    st.rerun()
        else:
            st.error("디깅에 실패했습니다. API 키나 파일 연결을 확인해 주세요.")

with col2:
    st.subheader("🎧 Now Playing Hub")

    track = st.session_state.current_track
    if track:
        # 고화질 공식 커버 아트 및 곡 정보 카드 출력
        st.image(track["album_art"], use_container_width=True)
        
        st.markdown(f"""
            <div class="music-card">
                <h3 style='margin-top:0px; color:#FF4B4B;'>🎵 {track['title']}</h3>
                <p style='margin:4px 0;'><b>🎤 아티스트</b>: {track['artist']}</p>
                <p style='margin:4px 0;'><b>📅 발매년도</b>: {track['year']}</p>
                <p style='margin:4px 0;'><b>🏷️ 장르</b>: {track['genre']}</p>
            </div>
        """, unsafe_allow_html=True)

        # 유튜브 미디어 플레이어 로드
        st.video(f"https://www.youtube.com/watch?v={track['youtube_id']}")

        # 실시간 가사 1마디 Bold 효과 렌더링 존
        st.markdown("#### 🎙️ 실시간 디깅 가사 트래커")
        lyrics_placeholder = st.empty()

        # 하단 플레이리스트 제안 및 재생목록 묶음 내보내기 자동화 링크
        st.markdown("---")
        st.markdown("#### 🗂️ 관련 디깅 플레이리스트 제안")
        for p_song in track["playlist"]:
            p_cols = st.columns([1, 5])
            with p_cols[0]:
                st.markdown(f"[▶️](https://www.youtube.com/watch?v={p_song['id']})")
            with p_cols[1]:
                st.markdown(f"**{p_song['title']}** - {p_song['artist']}")
        
        # 유튜브 복수 영상 동시 재생 파라미터를 활용한 묶음 플레이리스트 생성 링크
        all_ids = [track["youtube_id"]] + [p["id"] for p in track["playlist"]]
        export_url = f"https://www.youtube.com/watch_videos?video_ids={','.join(all_ids)}"
        st.markdown("<br>", unsafe_allow_html=True)
        st.link_button("🚀 발견한 플레이리스트 내 YouTube 재생목록에 담기", export_url, use_container_width=True)

        # 가사 한 줄씩 하이라이트(Bold) 처리 시뮬레이션 인터벌 스케줄러 루프
        for idx, current_line in enumerate(track["lyrics"]):
            lyrics_html = ""
            for jdx, line_content in enumerate(track["lyrics"]):
                if jdx == idx:
                    # 현재 매칭 마디 가사를 빨간색 Bold 처리
                    lyrics_html += f"<p style='margin:0; font-size:16px; color:#FF4B4B;'><b>✨ {line_content}</b></p>"
                else:
                    # 지나갔거나 다가올 마디는 블러(투명도 0.5) 처리
                    lyrics_html += f"<p style='margin:0; font-size:14px; color:#777777; opacity:0.5;'>{line_content}</p>"
            
            lyrics_placeholder.markdown(f"<div class='lyrics-box'>{lyrics_html}</div>", unsafe_allow_html=True)
            time.sleep(3.0)  # 3초마다 다음 마디로 강조 이동
    else:
        st.info("왼쪽 대화창에 원하는 사운드 레이어나 무드를 던져보세요. AI Agent가 아카이빙을 시작합니다.")

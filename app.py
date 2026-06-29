# app.py 파일의 맨 아래 115번째 줄부터 끝까지의 블록이 아래와 정확히 일치하는지 확인하세요.
# 특히 st.rerun()들의 들여쓰기 위치가 아주 중요합니다!

    if user_input := st.chat_input("에이전트에게 톡 보내기..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.rerun()  # 유저가 입력했을 때만 단 한 번 새로고침 (벽면에 붙지 않고 if문 안쪽에 배치)
        
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
                st.rerun()  # AI 답변이 세션에 최종 저장되었을 때만 단 한 번 새로고침
    else:
        st.error("디깅에 실패했습니다. 코드를 재확인해 주세요.")

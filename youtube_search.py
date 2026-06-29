import os
from googleapiclient.discovery import build

def get_youtube_video_via_api(keyword):
    """
    키워드를 받아 유튜브에서 음악 동영상을 검색하고 
    영상 ID, 제목, 채널명, 고화질 썸네일을 반환합니다.
    """
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
            videoCategoryId="10"  # Music 카테고리
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
        print(f"유튜브 API 에러: {e}")
    return None
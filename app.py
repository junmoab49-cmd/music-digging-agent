import os
import streamlit as st
from dotenv import load_dotenv
from googleapiclient.discovery import build

# 에이전트 파일로부터 함수 가져오기
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

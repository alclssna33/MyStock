import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import os
import time
import json
import re
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# FinanceDataReader 선택적 임포트 (없어도 앱 실행 가능)
try:
    import FinanceDataReader as fdr
    FDR_AVAILABLE = True
except ImportError:
    FDR_AVAILABLE = False
    fdr = None

# 페이지 설정
st.set_page_config(
    page_title="나만의 주식 추적기",
    page_icon="📈",
    layout="wide"
)

# 모던 핀테크 스타일 CSS 주입
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700&display=swap');
    
    /* === 1. 전체 기본 텍스트 (흰색) === */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        font-family: 'Pretendard', sans-serif;
        color: #FFFFFF !important;
    }
    
    /* 기본 텍스트 요소들은 흰색 */
    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #FFFFFF;
    }

    /* === 2. 입력 필드 스타일 (배경 화이트, 글자 블랙) === */
    /* Input, Textarea 스타일 */
    input, textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        caret-color: #000000 !important;
    }

    /* === [핵심 수정] 3. Selectbox (종목선택, 기간선택, 삭제박스) === */
    /* Selectbox 컨테이너 (닫혀있을 때) */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    /* [중요] Selectbox 내부에 표시되는 '선택된 값' 강제 검은색 */
    /* 내부의 div, span, p 등 모든 텍스트 요소를 검은색으로 덮어씀 */
    div[data-baseweb="select"] > div * {
        color: #000000 !important;
    }
    
    /* Dropdown 메뉴 (펼쳤을 때 리스트) */
    div[data-baseweb="popover"],
    div[data-baseweb="menu"],
    ul[data-baseweb="menu"] {
        background-color: #FFFFFF !important;
    }
    
    /* Dropdown 메뉴 내부 텍스트 */
    div[data-baseweb="popover"] *,
    div[data-baseweb="menu"] *,
    ul[data-baseweb="menu"] * {
        color: #000000 !important;
    }

    /* === 4. 달력(Calendar) 스타일 === */
    div[data-baseweb="calendar"] {
        background-color: #FFFFFF !important;
    }
    div[data-baseweb="calendar"] * {
        color: #000000 !important;
    }
    
    /* === 4-1. 입력 필드 높이 통일 (상단 컨트롤 바 정렬) === */
    /* Selectbox 높이 통일 */
    div[data-baseweb="select"] > div {
        min-height: 38px !important;
        height: 38px !important;
        display: flex !important;
        align-items: center !important;
    }
    
    /* Date Input 높이 통일 */
    input[type="date"],
    input[type="text"],
    div[data-baseweb="input"] input {
        min-height: 38px !important;
        height: 38px !important;
        padding: 0 0.75rem !important;
    }
    
    /* Date Input 컨테이너 높이 통일 */
    div[data-baseweb="input"] {
        min-height: 38px !important;
        height: 38px !important;
    }
    
    div[data-baseweb="input"] > div {
        min-height: 38px !important;
        height: 38px !important;
    }
    
    /* Label 위치 조정 (모든 입력 필드의 라벨을 상단에 고정) */
    label {
        margin-bottom: 0.3rem !important;
    }
    
    /* Streamlit column 내부 컨테이너 정렬 */
    div[data-testid="column"] > div {
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-end !important;
    }

    /* === 5. 버튼 스타일 (수정됨: 실제 DOM 구조에 맞춤) === */
    
    /* [1. 공통 베이스] 모든 버튼 텍스트 색상 강제 */
    button,
    button p,
    button span {
        color: #FFFFFF !important;
    }
    
    /* [2. 기본 버튼] 모든 버튼에 먼저 적용 (보라색 - Default) */
    .stButton > button,
    div[data-testid="stDialog"] button,
    div[data-testid="stForm"] button,
    div[role="dialog"] button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button p,
    div[data-testid="stDialog"] button p,
    div[data-testid="stForm"] button p {
        color: #FFFFFF !important;
    }
    
    /* 기본 버튼 호버 효과 */
    .stButton > button:hover,
    div[data-testid="stDialog"] button:hover,
    div[data-testid="stForm"] button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4) !important;
    }
    
    /* [3. Secondary 버튼] 파란색 - 수정/취소 (실제 DOM 속성 사용) */
    button[data-testid="stBaseButton-secondaryFormSubmit"],
    button[kind="secondaryFormSubmit"],
    .stButton > button[data-testid="stBaseButton-secondaryFormSubmit"],
    .stButton > button[kind="secondaryFormSubmit"],
    div[data-testid="stDialog"] button[data-testid="stBaseButton-secondaryFormSubmit"],
    div[data-testid="stDialog"] button[kind="secondaryFormSubmit"],
    div[data-testid="stForm"] button[data-testid="stBaseButton-secondaryFormSubmit"],
    div[data-testid="stForm"] button[kind="secondaryFormSubmit"],
    div[role="dialog"] button[data-testid="stBaseButton-secondaryFormSubmit"],
    div[role="dialog"] button[kind="secondaryFormSubmit"] {
        background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%) !important;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #FFFFFF !important;
    }
    button[data-testid="stBaseButton-secondaryFormSubmit"]:hover,
    button[kind="secondaryFormSubmit"]:hover,
    .stButton > button[data-testid="stBaseButton-secondaryFormSubmit"]:hover,
    .stButton > button[kind="secondaryFormSubmit"]:hover,
    div[data-testid="stDialog"] button[data-testid="stBaseButton-secondaryFormSubmit"]:hover,
    div[data-testid="stDialog"] button[kind="secondaryFormSubmit"]:hover,
    div[data-testid="stForm"] button[data-testid="stBaseButton-secondaryFormSubmit"]:hover,
    div[data-testid="stForm"] button[kind="secondaryFormSubmit"]:hover,
    div[role="dialog"] button[data-testid="stBaseButton-secondaryFormSubmit"]:hover,
    div[role="dialog"] button[kind="secondaryFormSubmit"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(59, 130, 246, 0.4) !important;
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
    }
    button[data-testid="stBaseButton-secondaryFormSubmit"] p,
    button[kind="secondaryFormSubmit"] p,
    div[data-testid="stDialog"] button[data-testid="stBaseButton-secondaryFormSubmit"] p,
    div[data-testid="stDialog"] button[kind="secondaryFormSubmit"] p {
        color: #FFFFFF !important;
    }
    
    /* [4. Primary 버튼] 빨간색 - 기록/삭제/추가 (실제 DOM 속성 사용) */
    button[data-testid="stBaseButton-primaryFormSubmit"],
    button[kind="primaryFormSubmit"],
    .stButton > button[data-testid="stBaseButton-primaryFormSubmit"],
    .stButton > button[kind="primaryFormSubmit"],
    div[data-testid="stDialog"] button[data-testid="stBaseButton-primaryFormSubmit"],
    div[data-testid="stDialog"] button[kind="primaryFormSubmit"],
    div[data-testid="stForm"] button[data-testid="stBaseButton-primaryFormSubmit"],
    div[data-testid="stForm"] button[kind="primaryFormSubmit"],
    div[role="dialog"] button[data-testid="stBaseButton-primaryFormSubmit"],
    div[role="dialog"] button[kind="primaryFormSubmit"] {
        background: linear-gradient(135deg, #ef4444 0%, #f87171 100%) !important;
        box-shadow: 0 4px 6px rgba(239, 68, 68, 0.3) !important;
        border: none !important;
        color: #FFFFFF !important;
    }
    button[data-testid="stBaseButton-primaryFormSubmit"]:hover,
    button[kind="primaryFormSubmit"]:hover,
    .stButton > button[data-testid="stBaseButton-primaryFormSubmit"]:hover,
    .stButton > button[kind="primaryFormSubmit"]:hover,
    div[data-testid="stDialog"] button[data-testid="stBaseButton-primaryFormSubmit"]:hover,
    div[data-testid="stDialog"] button[kind="primaryFormSubmit"]:hover,
    div[data-testid="stForm"] button[data-testid="stBaseButton-primaryFormSubmit"]:hover,
    div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover,
    div[role="dialog"] button[data-testid="stBaseButton-primaryFormSubmit"]:hover,
    div[role="dialog"] button[kind="primaryFormSubmit"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(239, 68, 68, 0.4) !important;
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%) !important;
    }
    button[data-testid="stBaseButton-primaryFormSubmit"] p,
    button[kind="primaryFormSubmit"] p,
    div[data-testid="stDialog"] button[data-testid="stBaseButton-primaryFormSubmit"] p,
    div[data-testid="stDialog"] button[kind="primaryFormSubmit"] p {
        color: #FFFFFF !important;
    }
    
    /* === 뱃지 오버레이 버튼 숨기기 (종목별 현황) === */
    /* 뱃지가 있는 컨테이너 다음에 오는 버튼 컨테이너 타겟팅 */
    div[data-testid="stMarkdownContainer"]:has(.badge-overlay-visual) + div[data-testid="stButton"],
    div[data-testid="stMarkdownContainer"]:has(.badge-overlay-visual) ~ div[data-testid="stButton"],
    div:has(.badge-overlay-visual) + div[data-testid="stButton"],
    div:has(.badge-overlay-visual) ~ div[data-testid="stButton"] {
        margin-top: -48px !important;
        position: relative !important;
        z-index: 10 !important;
        pointer-events: auto !important;
    }
    
    /* 뱃지 오버레이 버튼 완전히 투명하게 */
    div[data-testid="stMarkdownContainer"]:has(.badge-overlay-visual) + div[data-testid="stButton"] button,
    div[data-testid="stMarkdownContainer"]:has(.badge-overlay-visual) ~ div[data-testid="stButton"] button,
    div:has(.badge-overlay-visual) + div[data-testid="stButton"] button,
    div:has(.badge-overlay-visual) ~ div[data-testid="stButton"] button {
        opacity: 0 !important;
        background: transparent !important;
        border: none !important;
        color: transparent !important;
        width: 100% !important;
        min-height: 48px !important;
        height: 48px !important;
        padding: 0 !important;
        margin: 0 !important;
        cursor: pointer !important;
        position: relative !important;
        z-index: 10 !important;
        pointer-events: auto !important;
    }
    
    /* 뱃지 시각적 요소는 클릭 불가 (버튼이 클릭 처리) */
    .badge-overlay-visual {
        pointer-events: none !important;
    }

    /* === 6. 사이드바 스타일 === */
    section[data-testid="stSidebar"] {
        background-color: #262730 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    /* 사이드바 입력창 예외 처리 (검은 글씨) */
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    /* 사이드바 Selectbox 예외 처리 */
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div * {
        color: #000000 !important;
    }
    /* 사이드바 버튼 - 기본 스타일 (data-testid 기반) */
    section[data-testid="stSidebar"] button:not([data-testid="baseButton-primary"]):not([data-testid="baseButton-secondary"]) {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: #FFFFFF !important;
    }

    /* === 7. '정보 수정하기' Expander 스타일 === */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #FFF9C4 0%, #FFE082 100%) !important;
        border: 2px solid #FFD54F !important;
        border-radius: 10px !important;
        color: #5D4037 !important;
    }
    .streamlit-expanderHeader p, 
    .streamlit-expanderHeader span,
    .streamlit-expanderHeader svg {
        color: #5D4037 !important;
        fill: #5D4037 !important;
    }
    [data-testid="stExpanderDetails"] {
        background: rgba(255, 249, 196, 0.1) !important;
        border: 1px solid #FFD54F !important;
    }
    
    /* === 8. 매수 계획 테이블 스타일 === */
    /* 날짜 입력 필드 스타일 */
    div[data-baseweb="calendar"] {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
    }
    
    /* 숫자 입력 필드 스타일 - 명확한 배경과 글자색 */
    div[data-baseweb="input"] input[type="number"],
    input[type="number"],
    input[type="text"][inputmode="numeric"] {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 6px !important;
        padding: 0.5rem !important;
    }
    
    input[type="number"]:focus,
    input[type="text"][inputmode="numeric"]:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* Streamlit number_input 컨테이너 */
    div[data-baseweb="input"] {
        background-color: transparent !important;
    }
    
    div[data-baseweb="input"] > div {
        background-color: #FFFFFF !important;
    }
    
    div[data-baseweb="input"] input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* number_input 내부 스타일 강제 적용 - +, - 버튼 완전히 숨기기 */
    /* 모든 number input의 스피너 버튼 숨기기 */
    input[type="number"]::-webkit-inner-spin-button,
    input[type="number"]::-webkit-outer-spin-button,
    div[data-baseweb="input"] input[type="number"]::-webkit-inner-spin-button,
    div[data-baseweb="input"] input[type="number"]::-webkit-outer-spin-button,
    div[data-baseweb="input"] input::-webkit-inner-spin-button,
    div[data-baseweb="input"] input::-webkit-outer-spin-button {
        -webkit-appearance: none !important;
        appearance: none !important;
        margin: 0 !important;
        display: none !important;
        opacity: 0 !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
    }
    
    /* Firefox에서도 스피너 숨기기 */
    input[type="number"],
    div[data-baseweb="input"] input[type="number"] {
        -moz-appearance: textfield !important;
    }
    
    /* BaseWeb input 컨테이너 내부의 모든 버튼 숨기기 (+, - 버튼) */
    div[data-baseweb="input"] button,
    div[data-baseweb="input"] > div > button,
    div[data-baseweb="input"] > div > div > button,
    div[data-baseweb="input"] > button,
    div[data-baseweb="input"] * button {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        position: absolute !important;
        left: -9999px !important;
    }
    
    /* Streamlit number_input의 증가/감소 버튼 숨기기 */
    button[aria-label*="increment"],
    button[aria-label*="decrement"],
    button[aria-label*="Increment"],
    button[aria-label*="Decrement"],
    button[data-baseweb*="increment"],
    button[data-baseweb*="decrement"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }
    
    /* BaseWeb NumberInput의 스피너 컨트롤 숨기기 */
    div[data-baseweb="input"] > div[role="button"],
    div[data-baseweb="input"] svg[data-baseweb="icon"],
    div[data-baseweb="input"] > div > div[role="button"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* 모든 number_input 관련 버튼 숨기기 (범용) */
    div[data-baseweb="input"] * button,
    div[data-baseweb="input"] button[type="button"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
    }
    
    /* Streamlit number_input의 모든 버튼 요소 숨기기 (최종) */
    div[data-baseweb="input"] > div > div > button,
    div[data-baseweb="input"] > div > button[type="button"],
    div[data-baseweb="input"] button[aria-label],
    div[data-baseweb="input"] button[title] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
    }
    
    /* BaseWeb input 내부의 모든 자식 요소 중 버튼 숨기기 */
    div[data-baseweb="input"] button[type="button"],
    div[data-baseweb="input"] > div > div > button {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
    }
    
    /* 매수 계획 카드 스타일 */
    div[data-testid="stContainer"] {
        background: transparent !important;
    }
    
    /* [5. 개별 버튼 스타일링] 필요시 아래에 특정 버튼만 추가 가능 */
    /* 예시:
    button[key="delete_button"] {
        background: linear-gradient(135deg, #ef4444 0%, #f87171 100%) !important;
        color: #FFFFFF !important;
    }
    */
    
    /* === 9. Dialog (팝업) 너비 조정 === */
    /* Streamlit Dialog 컨테이너 너비 확장 - 모든 가능한 선택자 */
    div[data-testid="stDialog"],
    div[role="dialog"],
    div[class*="dialog"],
    div[class*="Dialog"],
    section[data-testid="stDialog"],
    section[role="dialog"],
    /* BaseWeb Modal/Dialog 스타일 */
    div[data-baseweb="modal"],
    div[data-baseweb="Modal"],
    /* 일반적인 모달 클래스 */
    .modal,
    .Modal,
    [class*="modal"],
    [class*="Modal"] {
        max-width: 95vw !important;
        width: 95vw !important;
        min-width: 1400px !important;
    }
    
    /* Dialog 내부 컨텐츠 영역 */
    div[data-testid="stDialog"] > div,
    div[role="dialog"] > div,
    section[data-testid="stDialog"] > div,
    section[role="dialog"] > div {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* Dialog 내부의 Streamlit 컨테이너 */
    div[data-testid="stDialog"] div[data-testid="stVerticalBlock"],
    div[data-testid="stDialog"] div[data-testid="stHorizontalBlock"],
    div[role="dialog"] div[data-testid="stVerticalBlock"],
    div[role="dialog"] div[data-testid="stHorizontalBlock"],
    section[data-testid="stDialog"] div[data-testid="stVerticalBlock"],
    section[data-testid="stDialog"] div[data-testid="stHorizontalBlock"] {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* Dialog 내부의 컬럼 레이아웃 */
    div[data-testid="stDialog"] div[data-testid="column"],
    div[role="dialog"] div[data-testid="column"],
    section[data-testid="stDialog"] div[data-testid="column"] {
        max-width: 100% !important;
        flex: 1 1 auto !important;
    }
    
    /* Dialog 내부의 모든 컨테이너 */
    div[data-testid="stDialog"] div[data-testid="stContainer"],
    div[role="dialog"] div[data-testid="stContainer"],
    section[data-testid="stDialog"] div[data-testid="stContainer"] {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* === 10. Dialog (팝업) 다크모드 스타일 === */
    /* Dialog 배경색 - 다크모드 */
    div[data-testid="stDialog"],
    div[role="dialog"],
    section[data-testid="stDialog"],
    section[role="dialog"],
    div[data-baseweb="modal"],
    div[data-baseweb="Modal"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
        color: #FFFFFF !important;
    }
    
    /* Dialog 내부 모든 텍스트 - 흰색 (버튼과 입력 필드 제외) */
    div[data-testid="stDialog"] *:not(button):not(button *):not(input):not(input *):not(textarea):not(textarea *),
    div[role="dialog"] *:not(button):not(button *):not(input):not(input *):not(textarea):not(textarea *),
    section[data-testid="stDialog"] *:not(button):not(button *):not(input):not(input *):not(textarea):not(textarea *),
    section[role="dialog"] *:not(button):not(button *):not(input):not(input *):not(textarea):not(textarea *) {
        color: #FFFFFF !important;
    }
    
    /* Dialog 내부 입력 필드 텍스트 색상 강제 (전역 스타일보다 우선) */
    div[data-testid="stDialog"] input,
    div[data-testid="stDialog"] textarea,
    div[data-testid="stDialog"] input *,
    div[data-testid="stDialog"] textarea *,
    div[role="dialog"] input,
    div[role="dialog"] textarea,
    div[role="dialog"] input *,
    div[role="dialog"] textarea * {
        color: #000000 !important;
    }
    
    /* Dialog 내부 제목, 헤더 */
    div[data-testid="stDialog"] h1,
    div[data-testid="stDialog"] h2,
    div[data-testid="stDialog"] h3,
    div[data-testid="stDialog"] h4,
    div[data-testid="stDialog"] h5,
    div[data-testid="stDialog"] h6,
    div[data-testid="stDialog"] p,
    div[data-testid="stDialog"] span,
    div[data-testid="stDialog"] label,
    div[role="dialog"] h1,
    div[role="dialog"] h2,
    div[role="dialog"] h3,
    div[role="dialog"] h4,
    div[role="dialog"] h5,
    div[role="dialog"] h6,
    div[role="dialog"] p,
    div[role="dialog"] span,
    div[role="dialog"] label {
        color: #FFFFFF !important;
    }
    
    /* Dialog 내부 컨테이너 배경 - 투명 또는 다크 */
    div[data-testid="stDialog"] div[data-testid="stVerticalBlock"],
    div[data-testid="stDialog"] div[data-testid="stHorizontalBlock"],
    div[data-testid="stDialog"] div[data-testid="stContainer"],
    div[role="dialog"] div[data-testid="stVerticalBlock"],
    div[role="dialog"] div[data-testid="stHorizontalBlock"],
    div[role="dialog"] div[data-testid="stContainer"] {
        background: transparent !important;
    }
    
    /* Dialog 내부 입력 필드 - 흰색 배경, 검은색 글자 (입력창은 밝게 유지) */
    div[data-testid="stDialog"] input,
    div[data-testid="stDialog"] textarea,
    div[role="dialog"] input,
    div[role="dialog"] textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* Dialog 내부 Selectbox - 흰색 배경, 검은색 글자 */
    div[data-testid="stDialog"] div[data-baseweb="select"] > div,
    div[role="dialog"] div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    div[data-testid="stDialog"] div[data-baseweb="select"] > div *,
    div[role="dialog"] div[data-baseweb="select"] > div * {
        color: #000000 !important;
    }
    
    /* Dialog 내부 달력 - 흰색 배경, 검은색 글자 */
    div[data-testid="stDialog"] div[data-baseweb="calendar"],
    div[role="dialog"] div[data-baseweb="calendar"] {
        background-color: #FFFFFF !important;
    }
    
    div[data-testid="stDialog"] div[data-baseweb="calendar"] *,
    div[role="dialog"] div[data-baseweb="calendar"] * {
        color: #000000 !important;
    }
    
    /* Dialog 내부 기본 버튼 - Primary/Secondary가 아닌 경우만 (data-testid 기반) */
    div[data-testid="stDialog"] .stButton > button:not([data-testid="baseButton-primary"]):not([data-testid="baseButton-secondary"]):not([type="submit"]),
    div[role="dialog"] .stButton > button:not([data-testid="baseButton-primary"]):not([data-testid="baseButton-secondary"]):not([type="submit"]) {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: #FFFFFF !important;
    }
    
    /* Dialog 내부 메트릭 (Metric) - 흰색 텍스트 */
    div[data-testid="stDialog"] [data-testid="stMetricValue"],
    div[data-testid="stDialog"] [data-testid="stMetricLabel"],
    div[role="dialog"] [data-testid="stMetricValue"],
    div[role="dialog"] [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
    }
    
    /* Dialog 내부 Progress Bar 배경 */
    div[data-testid="stDialog"] [data-testid="stProgressBar"] > div,
    div[role="dialog"] [data-testid="stProgressBar"] > div {
        background-color: rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Dialog 내부 Markdown 텍스트 */
    div[data-testid="stDialog"] div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stDialog"] div[data-testid="stMarkdownContainer"] span,
    div[data-testid="stDialog"] div[data-testid="stMarkdownContainer"] div,
    div[role="dialog"] div[data-testid="stMarkdownContainer"] p,
    div[role="dialog"] div[data-testid="stMarkdownContainer"] span,
    div[role="dialog"] div[data-testid="stMarkdownContainer"] div {
        color: #FFFFFF !important;
    }
    
    /* Dialog 내부 Info/Success/Warning 메시지 배경 조정 */
    div[data-testid="stDialog"] [data-testid="stNotification"],
    div[role="dialog"] [data-testid="stNotification"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Dialog 내부 Divider */
    div[data-testid="stDialog"] hr,
    div[data-testid="stDialog"] [data-testid="stDivider"],
    div[role="dialog"] hr,
    div[role="dialog"] [data-testid="stDivider"] {
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# Google Sheets 설정
SPREADSHEET_NAME = "Integrated_Stock_DB" 
SCOPE = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

# Google Sheets 클라이언트 가져오기 (캐싱)
@st.cache_resource
def get_google_sheets_client():
    """Google Sheets API 클라이언트를 반환합니다."""
    try:
        # Streamlit secrets에서 가져오기 시도
        if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
            creds_dict = dict(st.secrets['gcp_service_account'])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        # secrets.json 파일에서 가져오기
        elif os.path.exists("secrets.json"):
            creds = ServiceAccountCredentials.from_json_keyfile_name("secrets.json", SCOPE)
        else:
            st.error("❌ Google Sheets 인증 정보를 찾을 수 없습니다.\n\n"
                    "다음 중 하나를 설정해주세요:\n"
                    "1. Streamlit secrets에 'gcp_service_account' 키 추가\n"
                    "2. 프로젝트 루트에 'secrets.json' 파일 추가")
            st.stop()
        
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"❌ Google Sheets 연결 실패: {str(e)}\n\n"
                "secrets.json 파일이 올바른 형식인지 확인해주세요.")
        st.stop()

# Google Sheets 초기화
def init_google_sheet():
    """Google Sheets 스프레드시트와 워크시트를 초기화합니다."""
    try:
        client = get_google_sheets_client()
        
        # 스프레드시트 찾기 또는 생성
        try:
            spreadsheet = client.open(SPREADSHEET_NAME)
        except gspread.SpreadsheetNotFound:
            # 스프레드시트가 없으면 생성
            spreadsheet = client.create(SPREADSHEET_NAME)
            st.info(f"✅ 새 스프레드시트 '{SPREADSHEET_NAME}'가 생성되었습니다.")
        
        # 통합 워크시트 찾기 또는 생성 (Stocks 시트로 통합)
        try:
            worksheet = spreadsheet.worksheet("Stocks")
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title="Stocks", rows=1000, cols=20)
        
        # 헤더 확인 및 추가 (통합 구조)
        headers = worksheet.row_values(1)
        expected_columns = ["Symbol", "Name", "InterestDate", "Note", "MarketCap", "Installments", "Category", "BuyTransactions", "SellTransactions", "ChangeRate"]
        
        if not headers or headers != expected_columns:
            # 헤더 업데이트 (기존 데이터 보존)
            if headers and len(headers) < len(expected_columns):
                # 기존 헤더에 없는 컬럼만 추가
                for col in expected_columns:
                    if col not in headers:
                        headers.append(col)
                worksheet.update('A1', [headers])
            elif not headers:
                # 헤더가 없으면 추가만 (데이터는 보존)
                worksheet.insert_row(expected_columns, 1)
            else:
                # 헤더가 완전히 다르면 경고만 (데이터는 보존)
                st.warning("⚠️ Google Sheets 헤더가 예상과 다릅니다. 수동으로 확인해주세요.")
                # 헤더만 업데이트 (데이터는 보존)
                worksheet.update('A1', [expected_columns])
        
        return spreadsheet, worksheet
    except Exception as e:
        st.error(f"❌ Google Sheets 초기화 실패: {str(e)}")
        st.stop()

# Google Sheets에서 데이터 읽기 (통합 시트)
@st.cache_data(ttl=60)  # 1분 캐싱 (데이터 변경 시 빠른 반영)
def load_stocks():
    """Google Sheets에서 종목 데이터를 로드합니다 (통합 시트)."""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet("Stocks")
        
        # 모든 데이터 가져오기
        records = worksheet.get_all_records()
        
        if not records:
            # 빈 DataFrame 반환 (헤더만 있는 경우)
            columns = ["Symbol", "Name", "InterestDate", "Note", "MarketCap", "Installments", "Category", "BuyTransactions", "SellTransactions", "ChangeRate"]
            return pd.DataFrame(columns=columns)
        
        # DataFrame으로 변환
        df = pd.DataFrame(records)
        
        # 빈 값 처리 (Google Sheets는 빈 셀을 빈 문자열로 반환)
        df = df.replace("", pd.NA)
        
        # BuyTransactions, SellTransactions가 문자열이면 JSON 파싱 (나중에 사용 시)
        # 여기서는 그대로 유지 (필요시 파싱)
        
        return df
    except Exception as e:
        st.error(f"❌ 데이터 로드 실패: {str(e)}")
        # 빈 DataFrame 반환
        columns = ["Symbol", "Name", "InterestDate", "Note", "MarketCap", "Installments", "Category", "BuyTransactions", "SellTransactions", "ChangeRate"]
        return pd.DataFrame(columns=columns)

# Google Sheets에 데이터 저장 (통합 시트)
def save_stocks(df):
    """DataFrame을 Google Sheets에 저장합니다 (통합 시트)."""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet("Stocks")
        
        # 안전장치: df가 비어있으면 저장하지 않음
        if df.empty:
            st.warning("⚠️ 저장할 데이터가 없습니다. 데이터가 사라지는 것을 방지하기 위해 저장을 건너뜁니다.")
            return
        
        # 기존 ChangeRate 값 보존 (Symbol 기준)
        # Apps Script가 업데이트한 최신 ChangeRate 값을 유지하기 위해
        existing_df = load_stocks()
        change_rate_map = {}
        if 'ChangeRate' in existing_df.columns and 'Symbol' in existing_df.columns:
            for _, row in existing_df.iterrows():
                symbol = row.get('Symbol', '')
                change_rate = row.get('ChangeRate', '')
                if symbol and pd.notna(change_rate) and change_rate != '':
                    change_rate_map[str(symbol)] = change_rate
        
        # 빈 값 처리 (pd.NA를 빈 문자열로 변환)
        df = df.fillna("")
        
        # BuyTransactions, SellTransactions가 리스트/딕셔너리면 JSON 문자열로 변환
        if 'BuyTransactions' in df.columns:
            df['BuyTransactions'] = df['BuyTransactions'].apply(
                lambda x: json.dumps(x) if isinstance(x, (list, dict)) else (x if x else '[]')
            )
        if 'SellTransactions' in df.columns:
            df['SellTransactions'] = df['SellTransactions'].apply(
                lambda x: json.dumps(x) if isinstance(x, (list, dict)) else (x if x else '[]')
            )
        
        # ChangeRate 컬럼 처리
        if 'ChangeRate' not in df.columns:
            df['ChangeRate'] = ""
        
        # 기존 ChangeRate 값 복원 (Symbol 기준)
        # Python에서 수정한 데이터가 있으면 그것을 사용, 없으면 기존 값 유지
        if 'Symbol' in df.columns:
            df['ChangeRate'] = df.apply(
                lambda row: change_rate_map.get(str(row['Symbol']), row.get('ChangeRate', '')),
                axis=1
            )
        
        # 헤더 포함 전체 데이터 준비
        values = [df.columns.tolist()] + df.values.tolist()
        
        # 안전장치: values가 비어있거나 헤더만 있으면 저장하지 않음
        if len(values) <= 1:
            st.warning("⚠️ 저장할 데이터가 없습니다. 데이터가 사라지는 것을 방지하기 위해 저장을 건너뜁니다.")
            return
        
        # 기존 데이터 지우고 새 데이터 쓰기 (안전하게)
        try:
            worksheet.clear()
            worksheet.update(values, value_input_option='USER_ENTERED')
        except Exception as update_error:
            # 업데이트 실패 시 기존 데이터 복원 시도
            st.error(f"❌ 데이터 저장 중 오류 발생: {str(update_error)}")
            # 기존 데이터 다시 로드하여 복원 시도
            if not existing_df.empty:
                try:
                    restore_values = [existing_df.columns.tolist()] + existing_df.fillna("").values.tolist()
                    worksheet.clear()
                    worksheet.update(restore_values, value_input_option='USER_ENTERED')
                    st.info("기존 데이터로 복원을 시도했습니다.")
                except:
                    pass
            raise
        
        # 캐시 무효화 (다음 로드 시 최신 데이터 가져오기)
        load_stocks.clear()
        load_split_purchase_data.clear()  # 분할 매수 플래너 캐시도 초기화
        
    except Exception as e:
        st.error(f"❌ 데이터 저장 실패: {str(e)}")
        raise

# 주가 데이터 가져오기 (하이브리드 방식: FinanceDataReader + yfinance)
@st.cache_data(ttl=7200)  # 2시간 캐싱 (rate limiting 방지)
def get_stock_data(symbol):
    # symbol 유효성 검사
    if symbol is None:
        return None
    
    # symbol을 문자열로 변환 (0으로 시작하는 종목번호 보존)
    try:
        # 숫자로 변환되면 앞의 0이 사라지므로, 먼저 문자열로 변환
        if isinstance(symbol, (int, float)):
            # 숫자인 경우 6자리로 패딩 (앞에 0 추가)
            symbol_str = str(int(symbol)).zfill(6)
        else:
            symbol_str = str(symbol).strip()
        
        if not symbol_str:
            return None
    except Exception:
        return None
    
    max_retries = 3
    retry_delay = 2  # 초기 지연 시간 (초)
    
    # 1. 한국 종목 코드 정제 (숫자 6자리 추출, 앞의 0 보존)
    clean_symbol = symbol_str.upper()
    is_korean = False
    market_suffix = None  # .KS 또는 .KQ 저장
    
    # .KS, .KQ 제거 후 순수 숫자인지 확인
    if clean_symbol.endswith('.KS') or clean_symbol.endswith('.KQ'):
        if clean_symbol.endswith('.KS'):
            market_suffix = '.KS'
        elif clean_symbol.endswith('.KQ'):
            market_suffix = '.KQ'
        
        temp_symbol = clean_symbol.replace('.KS', '').replace('.KQ', '')
        if temp_symbol.isdigit():
            # 6자리로 패딩 (앞에 0 추가)
            clean_symbol = temp_symbol.zfill(6)
            is_korean = True
    elif clean_symbol.isdigit():
        # 숫자인 경우 6자리로 패딩
        clean_symbol = clean_symbol.zfill(6)
        is_korean = True
    
    for attempt in range(max_retries):
        try:
            # 요청 간 지연 (rate limiting 방지)
            if attempt > 0:
                time.sleep(retry_delay * (attempt + 1))  # 지수 백오프
            
            df = None
            
            # 2. FinanceDataReader 사용 (한국 종목)
            if is_korean and FDR_AVAILABLE:
                try:
                    df = fdr.DataReader(clean_symbol)
                    # FinanceDataReader는 인덱스가 Date가 아닐 수 있으므로 확인
                    if df is not None and not df.empty:
                        # 인덱스 이름이 없거나 다른 경우 'Date'로 설정
                        if df.index.name is None or df.index.name != 'Date':
                            df.index.name = 'Date'
                except Exception as fdr_error:
                    # FinanceDataReader 실패 시 yfinance로 폴백
                    df = None
            
            # 3. yfinance 사용 (미국 종목 또는 FDR 실패 시)
            if df is None or df.empty:
                # yfinance는 .KS/.KQ가 필요할 수 있으므로 원본 symbol 사용 시도
                # 한국 종목인 경우 접미사 추가
                yf_symbol = symbol_str
                if is_korean:
                    if market_suffix:
                        # 원본에 접미사가 있었으면 그대로 사용
                        yf_symbol = clean_symbol + market_suffix
                        ticker = yf.Ticker(yf_symbol)
                        df = ticker.history(period="max")
                    else:
                        # 접미사가 없으면 FinanceDataReader가 실패했으므로
                        # .KS와 .KQ를 모두 시도 (먼저 .KS 시도)
                        yf_symbol = clean_symbol + '.KS'
                        ticker = yf.Ticker(yf_symbol)
                        df = ticker.history(period="max")
                        
                        # .KS로 실패하면 .KQ 시도
                        if df is None or df.empty:
                            yf_symbol = clean_symbol + '.KQ'
                            ticker = yf.Ticker(yf_symbol)
                            df = ticker.history(period="max")
                else:
                    # 한국 종목이 아니면 원본 그대로 사용
                    ticker = yf.Ticker(yf_symbol)
                    df = ticker.history(period="max")
            
            # 빈 데이터 체크
            if df is None or df.empty:
                if attempt < max_retries - 1:
                    continue
                # 오류 메시지 숨김
                return None
            
            # 4. 데이터 표준화 (차트 호환성 유지)
            # 인덱스 이름 'Date'로 통일
            if df.index.name != 'Date':
                df.index.name = 'Date'
            
            # 타임존 제거 (yfinance는 타임존이 있고, fdr은 없을 수 있음)
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            # 날짜 정규화 (시간 제거)
            df.index = pd.to_datetime(df.index).normalize()
            
            # 컬럼명 표준화 (대소문자 통일: Open, High, Low, Close, Volume)
            if not df.empty:
                column_mapping = {}
                for col in df.columns:
                    col_lower = str(col).lower()
                    if col_lower in ['open', '시가']:
                        column_mapping[col] = 'Open'
                    elif col_lower in ['high', '고가']:
                        column_mapping[col] = 'High'
                    elif col_lower in ['low', '저가']:
                        column_mapping[col] = 'Low'
                    elif col_lower in ['close', '종가']:
                        column_mapping[col] = 'Close'
                    elif col_lower in ['volume', '거래량']:
                        column_mapping[col] = 'Volume'
                
                if column_mapping:
                    df = df.rename(columns=column_mapping)
            
            return df
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Rate limiting 오류 감지
            if "too many requests" in error_msg or "rate limit" in error_msg or "429" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # 지수 백오프
                    # 오류 메시지 숨김 (조용히 재시도)
                    time.sleep(wait_time)
                    continue
                else:
                    # 최종 실패 시에도 오류 메시지 숨김
                    return None
            
            # 기타 오류
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                # 오류 메시지 숨김
                return None
    
    return None

# 당일 상승률 계산 함수
@st.cache_data(ttl=300)  # 5분 캐싱
def get_daily_change(symbol):
    """당일 상승률을 계산합니다."""
    try:
        # API 요청 전 지연 (rate limit 방지)
        time.sleep(1.0)  # 1초로 증가
        
        stock_df = get_stock_data(symbol)
        if stock_df is None or stock_df.empty:
            return None
        
        # 최신 데이터 2개 (당일, 전일)
        if len(stock_df) < 2:
            return None
        
        latest = stock_df.iloc[-1]
        previous = stock_df.iloc[-2]
        
        if 'Close' not in latest or 'Close' not in previous:
            return None
        
        prev_close = previous['Close']
        curr_close = latest['Close']
        
        if pd.isna(prev_close) or pd.isna(curr_close) or prev_close == 0:
            return None
        
        change_pct = ((curr_close - prev_close) / prev_close) * 100
        return change_pct
    except Exception as e:
        return None

# ==========================================
# 분할 매수 플래너 관련 함수들
# ==========================================

# 분할 매수 플래너 데이터 로드 (통합 시트 사용)
@st.cache_data(ttl=60)
def load_split_purchase_data():
    """통합 Stocks 시트에서 분할 매수 플래너 데이터를 로드합니다."""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        
        try:
            ws = spreadsheet.worksheet("Stocks")
            records = ws.get_all_records()
            
            if not records:
                return pd.DataFrame(columns=["Symbol", "Name", "InterestDate", "Note", "MarketCap", "Installments", "Category", "BuyTransactions", "SellTransactions"])
            
            df = pd.DataFrame(records)
            
            # MarketCap이나 Installments가 있는 종목만 필터링 (분할 매수 플래너용)
            # 또는 모든 데이터 반환 (필터링은 UI에서 처리)
            return df
        except gspread.WorksheetNotFound:
            # 워크시트가 없으면 생성 (init_google_sheet에서 처리되지만 안전장치)
            ws = spreadsheet.add_worksheet(title="Stocks", rows=1000, cols=20)
            headers = ["Symbol", "Name", "InterestDate", "Note", "MarketCap", "Installments", "Category", "BuyTransactions", "SellTransactions"]
            ws.append_row(headers)
            return pd.DataFrame(columns=headers)
    except Exception as e:
        st.error(f"❌ 분할 매수 데이터 로드 실패: {str(e)}")
        return pd.DataFrame(columns=["Symbol", "Name", "InterestDate", "Note", "MarketCap", "Installments", "Category", "BuyTransactions", "SellTransactions"])

# 분할 매수 플래너 데이터 저장 (통합 시트 사용)
def save_split_purchase_data(df):
    """통합 Stocks 시트에 분할 매수 플래너 데이터를 저장합니다."""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        ws = spreadsheet.worksheet("Stocks")
        
        # 전체 데이터 로드
        all_df = load_stocks()
        
        # 기존 ChangeRate 값 보존 (Symbol 기준)
        # Apps Script가 업데이트한 최신 ChangeRate 값을 유지하기 위해
        change_rate_map = {}
        if 'ChangeRate' in all_df.columns and 'Symbol' in all_df.columns:
            for _, row in all_df.iterrows():
                symbol = row.get('Symbol', '')
                change_rate = row.get('ChangeRate', '')
                if symbol and pd.notna(change_rate) and change_rate != '':
                    change_rate_map[str(symbol)] = change_rate
        
        # JSON 컬럼을 문자열로 변환
        df = df.copy()
        if 'BuyTransactions' in df.columns:
            df['BuyTransactions'] = df['BuyTransactions'].apply(
                lambda x: json.dumps(x) if isinstance(x, (list, dict)) else (x if x else '[]')
            )
        if 'SellTransactions' in df.columns:
            df['SellTransactions'] = df['SellTransactions'].apply(
                lambda x: json.dumps(x) if isinstance(x, (list, dict)) else (x if x else '[]')
            )
        
        df = df.fillna("")
        
        # ChangeRate 컬럼 처리
        if 'ChangeRate' not in df.columns:
            df['ChangeRate'] = ""
        
        # 기존 ChangeRate 값 복원 (Symbol 기준)
        if 'Symbol' in df.columns:
            df['ChangeRate'] = df.apply(
                lambda row: change_rate_map.get(str(row['Symbol']), row.get('ChangeRate', '')),
                axis=1
            )
        
        # Symbol 기준으로 기존 데이터 업데이트 또는 추가
        for idx, row in df.iterrows():
            symbol = row.get('Symbol', '')
            if symbol:
                # 기존 데이터에서 해당 Symbol 찾기
                mask = all_df['Symbol'] == symbol
                if mask.any():
                    # 업데이트 (ChangeRate는 보존)
                    for col in row.index:
                        if col != 'ChangeRate':  # ChangeRate는 제외하고 업데이트
                            all_df.loc[mask, col] = row[col]
                    # ChangeRate가 없거나 비어있으면 기존 값 유지
                    if 'ChangeRate' in row.index and pd.notna(row.get('ChangeRate', '')) and row.get('ChangeRate', '') != '':
                        all_df.loc[mask, 'ChangeRate'] = row['ChangeRate']
                else:
                    # 새 행 추가
                    all_df = pd.concat([all_df, pd.DataFrame([row])], ignore_index=True)
        
        # 빈 값 처리
        all_df = all_df.fillna("")
        
        # 안전장치: all_df가 비어있으면 저장하지 않음
        if all_df.empty:
            st.warning("⚠️ 저장할 데이터가 없습니다. 데이터가 사라지는 것을 방지하기 위해 저장을 건너뜁니다.")
            return
        
        # 전체 데이터 저장
        values = [all_df.columns.tolist()] + all_df.values.tolist()
        
        # 안전장치: values가 비어있거나 헤더만 있으면 저장하지 않음
        if len(values) <= 1:
            st.warning("⚠️ 저장할 데이터가 없습니다. 데이터가 사라지는 것을 방지하기 위해 저장을 건너뜁니다.")
            return
        
        # 기존 데이터 백업 (복원용)
        backup_df = all_df.copy()
        
        # 전체 데이터 저장 (안전하게)
        try:
            ws.clear()
            ws.update(values, value_input_option='USER_ENTERED')
        except Exception as update_error:
            # 업데이트 실패 시 기존 데이터 복원 시도
            st.error(f"❌ 데이터 저장 중 오류 발생: {str(update_error)}")
            # 백업 데이터로 복원 시도
            if not backup_df.empty:
                try:
                    restore_values = [backup_df.columns.tolist()] + backup_df.fillna("").values.tolist()
                    ws.clear()
                    ws.update(restore_values, value_input_option='USER_ENTERED')
                    st.info("기존 데이터로 복원을 시도했습니다.")
                except:
                    pass
            raise
        
        # 캐시 무효화
        load_stocks.clear()
        load_split_purchase_data.clear()
    except Exception as e:
        st.error(f"❌ 분할 매수 데이터 저장 실패: {str(e)}")
        raise

# 초기화
init_google_sheet()

# 새 종목 추가 콜백 함수
def add_stock_callback():
    """새 종목 추가 폼 제출 시 실행되는 콜백 함수"""
    # session_state에서 값 가져오기
    symbol = st.session_state.get("symbol_input", "")
    name = st.session_state.get("name_input", "")
    interest_date = st.session_state.get("interest_date_input", None)
    note = st.session_state.get("note_input", "")
    
    if symbol and name:
        df = load_stocks()
        
        # 중복 체크: 대소문자 무시, 공백 제거 비교
        symbol_normalized = symbol.strip().upper()
        existing_symbols = df['Symbol'].astype(str).str.strip().str.upper()
        
        if symbol_normalized in existing_symbols.values:
            st.session_state["add_result"] = {"type": "error", "message": "이미 등록된 종목입니다."}
        else:
            new_row = {
                "Symbol": symbol_normalized,
                "Name": name,
                "InterestDate": interest_date.strftime("%Y-%m-%d") if interest_date else "",
                "Note": note if note else "",
                "MarketCap": "",  # 관심종목이므로 비워둠
                "Installments": "",  # 관심종목이므로 비워둠
                "Category": "",  # 관심종목이므로 비워둠
                "BuyTransactions": "[]",
                "SellTransactions": "[]"
            }
            
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_stocks(df)
            
            # 성공 시 입력값 초기화
            st.session_state["symbol_input"] = ""
            st.session_state["name_input"] = ""
            st.session_state["interest_date_input"] = None
            st.session_state["note_input"] = ""
            
            st.session_state["add_result"] = {"type": "success", "message": f"{name} ({symbol}) 종목이 추가되었습니다!", "rerun": True}
    else:
        st.session_state["add_result"] = {"type": "error", "message": "티커와 종목명은 필수 입력 항목입니다."}

# 사이드바
with st.sidebar:
    st.header("📊 종목 관리")
    
    # 새 종목 추가
    st.subheader("새 종목 추가하기")
    with st.form("add_stock_form"):
        symbol = st.text_input("티커 (예: AAPL, 005930.KS)", key="symbol_input")
        name = st.text_input("종목명", key="name_input")
        interest_date = st.date_input("관심일", value=None, key="interest_date_input")
        note = st.text_area("메모", key="note_input")
        
        st.form_submit_button("추가", on_click=add_stock_callback)
    
    # 메시지 출력 처리
    if "add_result" in st.session_state:
        result = st.session_state["add_result"]
        if result["type"] == "success":
            st.success(result["message"])
            if result.get("rerun", False):
                del st.session_state["add_result"]
                st.rerun()
        else:
            st.error(result["message"])
            del st.session_state["add_result"]
    
    st.divider()
    
    # 종목 삭제
    st.subheader("종목 삭제하기")
    df = load_stocks()
    if not df.empty:
        delete_options = [f"{row['Name']} ({row['Symbol']})" for _, row in df.iterrows()]
        # 가나다순 정렬
        delete_options = sorted(delete_options)
        selected_delete = st.selectbox("삭제할 종목 선택", delete_options, key="delete_select")
        
        if st.button("삭제", key="delete_button"):
            # 정렬된 리스트에서 선택된 항목의 Symbol 추출
            # 형식: "Name (Symbol)"
            selected_symbol = selected_delete.split("(")[1].rstrip(")")
            # 원본 df에서 해당 Symbol로 찾기
            mask = df['Symbol'] == selected_symbol
            deleted_name = df.loc[mask, 'Name'].values[0] if mask.any() else selected_delete.split("(")[0].strip()
            df = df[~mask].reset_index(drop=True)
            save_stocks(df)
            st.success(f"{deleted_name} 종목이 삭제되었습니다!")
            st.rerun()
    else:
        st.info("저장된 종목이 없습니다.")

# 메인 화면 - 탭 구조
tab1, tab2 = st.tabs(["📈 주식 추적기", "💰 분할 매수 플래너"])

# 탭 1: 주식 추적기
with tab1:
    st.title("📈 나만의 주식 추적기")
    
    df = load_stocks()

    if df.empty:
        st.info("사이드바에서 종목을 추가해주세요.")
    else:
        # 상단 컨트롤 바 (6단 구성 - 투자전략 드롭다운 추가)
        # 종목선택 박스 확대, 기간선택 박스 축소
        col1, col2, col3, col4, col5, col6 = st.columns([1, 1.2, 1.8, 0.8, 0.8, 0.6])
        
        with col1:
            # 카테고리 선택 (매수종목 / 관심종목)
            category = st.radio(
                "카테고리",
                options=["전체", "매수종목", "관심종목"],
                index=0,
                key="category_select",
                horizontal=True
            )
        
        with col2:
            # 투자전략 선택 (매수종목 선택 시에만 표시)
            if category == "매수종목":
                # 세션 상태 초기화 (카테고리가 변경되면)
                if 'strategy_select' not in st.session_state or st.session_state.get('prev_category') != category:
                    st.session_state['strategy_select'] = "Long"
                    st.session_state['prev_category'] = category
                
                strategy = st.selectbox(
                    "투자전략",
                    options=["전체", "Long", "Short", "Macro"],
                    index=1,  # default: Long
                    key="strategy_select"
                )
            else:
                strategy = "전체"  # 매수종목이 아닐 때는 전체로 설정
                if 'prev_category' in st.session_state:
                    st.session_state['prev_category'] = category
        
        with col3:
            # 종목 선택
            stock_options = [f"{row['Name']} ({row['Symbol']})" for _, row in df.iterrows()]
            
            # 카테고리 필터링 (BuyTransactions 사용)
            if category == "매수종목":
                filtered_options = []
                for idx, row in df.iterrows():
                    # BuyTransactions에 데이터가 있으면 매수종목
                    buy_txs_str = row.get('BuyTransactions', '[]')
                    has_buy = False
                    try:
                        if pd.notna(buy_txs_str) and str(buy_txs_str).strip():
                            buy_txs = json.loads(buy_txs_str) if isinstance(buy_txs_str, str) else buy_txs_str
                            if buy_txs and len(buy_txs) > 0:
                                has_buy = True
                    except:
                        pass
                    if has_buy:
                        # 투자전략 필터링 추가
                        if strategy == "전체":
                            filtered_options.append(f"{row['Name']} ({row['Symbol']})")
                        else:
                            row_category = row.get('Category', '')
                            if str(row_category).strip() == strategy:
                                filtered_options.append(f"{row['Name']} ({row['Symbol']})")
                if filtered_options:
                    stock_options = filtered_options
            elif category == "관심종목":
                filtered_options = []
                interest_stocks_data = []  # 종목 정보 저장 (상승률 계산용)
                for idx, row in df.iterrows():
                    # BuyTransactions가 비어있고 InterestDate가 있으면 관심종목
                    buy_txs_str = row.get('BuyTransactions', '[]')
                    has_buy = False
                    try:
                        if pd.notna(buy_txs_str) and str(buy_txs_str).strip():
                            buy_txs = json.loads(buy_txs_str) if isinstance(buy_txs_str, str) else buy_txs_str
                            if buy_txs and len(buy_txs) > 0:
                                has_buy = True
                    except:
                        pass
                    if not has_buy and pd.notna(row.get('InterestDate', '')) and str(row.get('InterestDate', '')).strip() != "":
                        stock_display = f"{row['Name']} ({row['Symbol']})"
                        filtered_options.append(stock_display)
                        # ChangeRate 컬럼에서 상승률 가져오기
                        change_rate = row.get('ChangeRate', None)
                        interest_stocks_data.append({
                            'display': stock_display,
                            'symbol': row['Symbol'],
                            'name': row['Name'],
                            'change_rate': change_rate  # Google Sheets의 J열 값
                        })
                if filtered_options:
                    stock_options = filtered_options
                    
                    # 상승률순 정렬 체크박스 (관심종목일 때만 표시)
                    # 이전 상태 확인
                    prev_sort_state = st.session_state.get("sort_by_change", False)
                    sort_by_change = st.checkbox("상승률순", key="sort_by_change", value=False)
                    
                    # 체크박스 상태가 변경되면 캐시 초기화
                    if prev_sort_state != sort_by_change:
                        # 관련 캐시 키들 제거
                        keys_to_remove = [k for k in st.session_state.keys() if k.startswith("interest_stocks_change_")]
                        for key in keys_to_remove:
                            if key in st.session_state:
                                del st.session_state[key]
                        if 'interest_stocks_cache_symbols' in st.session_state:
                            del st.session_state['interest_stocks_cache_symbols']
                    
                    if sort_by_change:
                        # interest_stocks_data가 유효한지 확인
                        if not interest_stocks_data or len(interest_stocks_data) == 0:
                            st.warning("관심종목이 없습니다.")
                            stock_options = sorted(filtered_options) if filtered_options else []
                        else:
                            # 세션 상태에 결과가 저장되어 있는지 확인
                            cache_key = f"interest_stocks_change_{len(interest_stocks_data)}"
                            
                            # 안전하게 symbols_key 생성
                            try:
                                symbols_list = [s.get('symbol', '') for s in interest_stocks_data if isinstance(s, dict) and 'symbol' in s]
                                symbols_key = tuple(sorted(symbols_list))
                            except Exception as e:
                                symbols_key = tuple()
                            
                            # 종목 목록이 변경되었는지 확인
                            if ('interest_stocks_cache_symbols' in st.session_state and 
                                st.session_state['interest_stocks_cache_symbols'] == symbols_key and
                                cache_key in st.session_state):
                                # 캐시된 결과 사용
                                stock_with_change = st.session_state[cache_key]
                            else:
                                # Google Sheets의 J열(ChangeRate)에서 상승률 가져오기
                                stock_with_change = []
                                
                                for stock_info in interest_stocks_data:
                                    try:
                                        # Google Sheets의 ChangeRate 값 사용
                                        change_rate = stock_info.get('change_rate', None)
                                        
                                        # change_rate를 숫자로 변환 시도
                                        change_pct = None
                                        if change_rate is not None and pd.notna(change_rate):
                                            try:
                                                # 문자열인 경우 숫자로 변환
                                                if isinstance(change_rate, str):
                                                    change_rate = change_rate.strip()
                                                    # % 기호 제거
                                                    if change_rate.endswith('%'):
                                                        change_rate = change_rate[:-1]
                                                    change_pct = float(change_rate)
                                                else:
                                                    change_pct = float(change_rate)
                                            except (ValueError, TypeError):
                                                change_pct = None
                                        
                                        if change_pct is not None:
                                            stock_with_change.append({
                                                'display': stock_info.get('display', ''),
                                                'symbol': stock_info.get('symbol', ''),
                                                'name': stock_info.get('name', ''),
                                                'change_pct': change_pct
                                            })
                                        else:
                                            # 상승률이 없는 경우 하단에 배치
                                            stock_with_change.append({
                                                'display': stock_info.get('display', ''),
                                                'symbol': stock_info.get('symbol', ''),
                                                'name': stock_info.get('name', ''),
                                                'change_pct': float('-inf')  # 정렬 시 맨 아래로
                                            })
                                    except Exception as e:
                                        # 에러 발생 시 해당 종목만 스킵
                                        if isinstance(stock_info, dict):
                                            stock_with_change.append({
                                                'display': stock_info.get('display', ''),
                                                'symbol': stock_info.get('symbol', ''),
                                                'name': stock_info.get('name', ''),
                                                'change_pct': float('-inf')
                                            })
                                
                                # 결과를 세션 상태에 저장
                                st.session_state[cache_key] = stock_with_change
                                st.session_state['interest_stocks_cache_symbols'] = symbols_key
                            
                            # 상승률순 정렬 (내림차순)
                            if stock_with_change:
                                stock_with_change.sort(key=lambda x: x.get('change_pct', float('-inf')), reverse=True)
                                
                                # 상승률 표시 형식으로 변환
                                stock_options = []
                                for stock_info in stock_with_change:
                                    change_pct = stock_info.get('change_pct', float('-inf'))
                                    if change_pct != float('-inf'):
                                        change_str = f"{change_pct:+.2f}%"
                                        # 빨간색으로 표시하기 위해 텍스트에 포함
                                        stock_options.append(f"{stock_info.get('name', '')} ({stock_info.get('symbol', '')}) {change_str}")
                                    else:
                                        stock_options.append(f"{stock_info.get('name', '')} ({stock_info.get('symbol', '')}) N/A")
                            else:
                                # stock_with_change가 비어있으면 기본 정렬 사용
                                stock_options = sorted(filtered_options) if filtered_options else []
                    else:
                        # 가나다순 정렬 (기본값)
                        stock_options = sorted(stock_options)
            
            # 가나다순 정렬 (상승률순이 아닐 때만)
            if category != "관심종목" or not st.session_state.get("sort_by_change", False):
                stock_options = sorted(stock_options)
            
            # 현재 선택된 종목부터 리스트가 시작되도록 재정렬
            # 카테고리나 정렬 방식이 변경되면 리셋
            current_category = st.session_state.get('prev_stock_select_category', '')
            current_sort = st.session_state.get('prev_stock_select_sort', False)
            
            # 카테고리 또는 정렬 방식이 변경되었는지 확인
            if current_category != category or current_sort != st.session_state.get("sort_by_change", False):
                # 변경되었으면 이전 선택 초기화
                st.session_state['prev_stock_select_category'] = category
                st.session_state['prev_stock_select_sort'] = st.session_state.get("sort_by_change", False)
            else:
                # 변경되지 않았으면 현재 선택된 종목 기준으로 재정렬
                if 'stock_select' in st.session_state and st.session_state['stock_select']:
                    current_selection = st.session_state['stock_select']
                    # 현재 선택된 종목이 리스트에 있는지 확인
                    if current_selection in stock_options:
                        current_index = stock_options.index(current_selection)
                        # 리스트 재정렬: 현재 선택 종목부터 시작
                        stock_options = stock_options[current_index:] + stock_options[:current_index]
            
            selected_stock = st.selectbox("종목 선택", stock_options, key="stock_select")
            
            # 상승률 표시를 위한 CSS 및 JavaScript (selectbox 내부 텍스트 색상 변경)
            if category == "관심종목" and st.session_state.get("sort_by_change", False):
                st.markdown("""
                <style>
                    /* selectbox 옵션 내 상승률 텍스트 색상 변경을 위한 스타일 */
                    div[data-baseweb="select"] > div {
                        color: #000000 !important;
                    }
                </style>
                <script>
                    // selectbox가 렌더링된 후 상승률 텍스트를 빨간색으로 변경
                    function updateChangeColor() {
                        const selectBox = document.querySelector('div[data-baseweb="select"]');
                        if (selectBox) {
                            // 드롭다운 메뉴 열기
                            const popover = document.querySelector('div[data-baseweb="popover"]');
                            if (popover) {
                                const options = popover.querySelectorAll('li, div[role="option"]');
                                options.forEach(function(option) {
                                    const text = option.textContent || option.innerText;
                                    // 상승률 패턴 찾기 (+X.XX% 또는 -X.XX%)
                                    const match = text.match(/([+-]?\\d+\\.\\d+%)/);
                                    if (match) {
                                        const originalText = text;
                                        const changeText = match[1];
                                        const beforeChange = originalText.substring(0, originalText.indexOf(changeText));
                                        const afterChange = originalText.substring(originalText.indexOf(changeText) + changeText.length);
                                        
                                        // HTML로 변경하여 빨간색 적용
                                        option.innerHTML = beforeChange + '<span style="color: #ef4444; font-weight: 600;">' + changeText + '</span>' + afterChange;
                                    }
                                });
                            }
                            
                            // 선택된 값도 업데이트
                            const selectedText = selectBox.textContent || selectBox.innerText;
                            const match = selectedText.match(/([+-]?\\d+\\.\\d+%)/);
                            if (match) {
                                const changeText = match[1];
                                const beforeChange = selectedText.substring(0, selectedText.indexOf(changeText));
                                const afterChange = selectedText.substring(selectedText.indexOf(changeText) + changeText.length);
                                // 선택된 값은 직접 수정하기 어려우므로 그대로 둠
                            }
                        }
                    }
                    
                    // DOM 로드 후 실행
                    if (document.readyState === 'loading') {
                        document.addEventListener('DOMContentLoaded', function() {
                            setTimeout(updateChangeColor, 200);
                        });
                    } else {
                        setTimeout(updateChangeColor, 200);
                    }
                    
                    // MutationObserver로 동적 추가 감지
                    const observer = new MutationObserver(function(mutations) {
                        setTimeout(updateChangeColor, 100);
                    });
                    observer.observe(document.body, {
                        childList: true,
                        subtree: true
                    });
                    
                    // selectbox 클릭 시에도 업데이트
                    document.addEventListener('click', function(e) {
                        if (e.target.closest('div[data-baseweb="select"]')) {
                            setTimeout(updateChangeColor, 100);
                        }
                    });
                </script>
                """, unsafe_allow_html=True)
        
        with col4:
            # 시작일
            start_date = st.date_input(
                "시작일",
                value=None,
                key="start_date"
            )
        
        with col5:
            # 종료일
            end_date = st.date_input(
                "종료일",
                value=None,
                key="end_date"
            )
        
        with col6:
            # 기간선택 박스
            period_options = {
                "6개월": 0.5,
                "1년": 1,
                "5년": 5,
                "10년": 10,
                "15년": 15
            }
            selected_period = st.selectbox(
                "기간선택",
                options=["선택안함"] + list(period_options.keys()),
                index=0,
                key="period_select"
            )
        
        if selected_stock:
            # 원본 df에서 선택된 종목 찾기
            # 상승률 텍스트가 포함되어 있을 수 있으므로 제거
            selected_name_symbol = selected_stock
            # 상승률 패턴 제거 (+X.XX% 또는 -X.XX% 또는 N/A)
            selected_name_symbol = re.sub(r'\s+[+-]?\d+\.\d+%', '', selected_name_symbol)  # 상승률 제거
            selected_name_symbol = re.sub(r'\s+N/A', '', selected_name_symbol)  # N/A 제거
            
            selected_row = None
            for idx, row in df.iterrows():
                if f"{row['Name']} ({row['Symbol']})" == selected_name_symbol:
                    selected_row = row
                    break
            
            if selected_row is not None:
                symbol = selected_row['Symbol']
                name = selected_row['Name']
                interest_date = selected_row.get('InterestDate', '')
                note = selected_row.get('Note', '')
                
                # BuyTransactions, SellTransactions 읽기 (JSON 파싱)
                buy_transactions = []
                sell_transactions = []
                try:
                    buy_txs_str = selected_row.get('BuyTransactions', '[]')
                    if pd.notna(buy_txs_str) and str(buy_txs_str).strip():
                        buy_transactions = json.loads(buy_txs_str) if isinstance(buy_txs_str, str) else buy_txs_str
                except:
                    buy_transactions = []
                
                try:
                    sell_txs_str = selected_row.get('SellTransactions', '[]')
                    if pd.notna(sell_txs_str) and str(sell_txs_str).strip():
                        sell_transactions = json.loads(sell_txs_str) if isinstance(sell_txs_str, str) else sell_txs_str
                except:
                    sell_transactions = []
                
                # 정보 수정하기 (상단 컨트롤 바 아래 별도 영역)
                with st.container():
                    st.markdown("""
                <style>
                .edit-container {
                    background: rgba(255, 255, 255, 0.05);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 1.5rem;
                    margin: 1rem 0;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }
                /* 정보 수정하기 Expander - 노란색 계열 (부드러운 노란색) */
                /* JavaScript로 동적 스타일 적용 */
                <script>
                function styleEditExpander() {
                    const expanders = document.querySelectorAll('[data-testid="stExpander"]');
                    expanders.forEach(expander => {
                        const header = expander.querySelector('.streamlit-expanderHeader');
                        if (header && header.textContent.includes('정보 수정하기')) {
                            header.style.background = 'linear-gradient(135deg, #FFF9C4 0%, #FFE082 100%)';
                            header.style.border = '2px solid #FFD54F';
                            header.style.borderRadius = '15px';
                            header.style.boxShadow = '0 4px 15px rgba(255, 213, 79, 0.3)';
                            header.style.color = '#5D4037';
                            header.style.fontWeight = '700';
                            const headerText = header.querySelectorAll('*');
                            headerText.forEach(el => {
                                if (el.tagName !== 'svg') {
                                    el.style.color = '#5D4037';
                                }
                            });
                            const content = expander.querySelector('[data-testid="stExpanderContent"]');
                            if (content) {
                                content.style.background = 'rgba(255, 249, 196, 0.4)';
                                content.style.borderRadius = '0 0 15px 15px';
                                content.style.padding = '1rem';
                                content.style.border = '1px solid rgba(255, 213, 79, 0.3)';
                            }
                        }
                    });
                }
                // 페이지 로드 시 및 DOM 변경 시 실행
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', styleEditExpander);
                } else {
                    styleEditExpander();
                }
                // Streamlit의 동적 업데이트를 감지
                const observer = new MutationObserver(styleEditExpander);
                observer.observe(document.body, { childList: true, subtree: true });
                </script>
                </style>
                    """, unsafe_allow_html=True)
                    with st.expander("📝 정보 수정하기", expanded=False):
                        # 날짜 데이터 변환 (문자열 -> date 객체)
                        def parse_date(date_str):
                            if pd.notna(date_str) and date_str != "":
                                try:
                                    return pd.to_datetime(date_str).date()
                                except:
                                    return None
                            return None
                        
                        edit_interest_date = st.date_input(
                            "관심일",
                            value=parse_date(interest_date),
                            key=f"edit_interest_date_{symbol}"
                        )
                        
                        # 매수일 입력 (BuyTransactions 사용)
                        st.write("**매수일**")
                        buy_date_inputs = []
                        buy_date_count = len(buy_transactions) if buy_transactions else 1
                        if buy_date_count == 0:
                            buy_date_count = 1
                        
                        # 세션 상태로 매수일 개수 관리
                        if f'buy_date_count_{symbol}' not in st.session_state:
                            st.session_state[f'buy_date_count_{symbol}'] = max(buy_date_count, 1)
                        
                        for i in range(st.session_state[f'buy_date_count_{symbol}']):
                            col_date, col_delete = st.columns([4, 1])
                            with col_date:
                                tx = buy_transactions[i] if i < len(buy_transactions) else {}
                                tx_date = tx.get('date', '') if isinstance(tx, dict) else ''
                                buy_date_inputs.append(st.date_input(
                                    f"매수일 {i+1}",
                                    value=parse_date(tx_date) if tx_date else None,
                                    key=f"edit_buy_date_{i}_{symbol}",
                                    label_visibility="collapsed"
                                ))
                            with col_delete:
                                if st.button("🗑️", key=f"delete_buy_date_{i}_{symbol}", help="삭제", type="secondary"):
                                    # BuyTransactions에서 해당 항목 삭제
                                    df_stocks = load_stocks()
                                    mask = df_stocks['Symbol'] == symbol
                                    if mask.any():
                                        try:
                                            buy_txs_str = df_stocks.loc[mask, 'BuyTransactions'].values[0]
                                            buy_txs = json.loads(buy_txs_str) if isinstance(buy_txs_str, str) else buy_txs_str
                                            if i < len(buy_txs):
                                                buy_txs.pop(i)
                                            df_stocks.loc[mask, 'BuyTransactions'] = json.dumps(buy_txs)
                                            save_stocks(df_stocks)
                                            st.success("삭제되었습니다!")
                                            time.sleep(0.5)
                                        except:
                                            pass
                                    # 개수 조정
                                    if st.session_state[f'buy_date_count_{symbol}'] > 0:
                                        st.session_state[f'buy_date_count_{symbol}'] -= 1
                                    if st.session_state[f'buy_date_count_{symbol}'] == 0:
                                        st.session_state[f'buy_date_count_{symbol}'] = 1
                                    st.rerun()
                        
                        # 매수일 추가 버튼
                        if st.button("➕ 매수일 추가", key=f"add_buy_date_{symbol}"):
                            if st.session_state[f'buy_date_count_{symbol}'] < 10:
                                st.session_state[f'buy_date_count_{symbol}'] += 1
                                st.rerun()
                            else:
                                st.warning("최대 10개까지 추가 가능합니다.")
                        
                        # 매도일 입력 (SellTransactions 사용)
                        st.write("**매도일**")
                        sell_date_inputs = []
                        sell_date_count = len(sell_transactions) if sell_transactions else 1
                        if sell_date_count == 0:
                            sell_date_count = 1
                        
                        # 세션 상태로 매도일 개수 관리
                        if f'sell_date_count_{symbol}' not in st.session_state:
                            st.session_state[f'sell_date_count_{symbol}'] = max(sell_date_count, 1)
                        
                        for i in range(st.session_state[f'sell_date_count_{symbol}']):
                            col_date, col_delete = st.columns([4, 1])
                            with col_date:
                                tx = sell_transactions[i] if i < len(sell_transactions) else {}
                                tx_date = tx.get('date', '') if isinstance(tx, dict) else ''
                                sell_date_inputs.append(st.date_input(
                                    f"매도일 {i+1}",
                                    value=parse_date(tx_date) if tx_date else None,
                                    key=f"edit_sell_date_{i}_{symbol}",
                                    label_visibility="collapsed"
                                ))
                            with col_delete:
                                if st.button("🗑️", key=f"delete_sell_date_{i}_{symbol}", help="삭제", type="secondary"):
                                    # SellTransactions에서 해당 항목 삭제
                                    df_stocks = load_stocks()
                                    mask = df_stocks['Symbol'] == symbol
                                    if mask.any():
                                        try:
                                            sell_txs_str = df_stocks.loc[mask, 'SellTransactions'].values[0]
                                            sell_txs = json.loads(sell_txs_str) if isinstance(sell_txs_str, str) else sell_txs_str
                                            if i < len(sell_txs):
                                                sell_txs.pop(i)
                                            df_stocks.loc[mask, 'SellTransactions'] = json.dumps(sell_txs)
                                            save_stocks(df_stocks)
                                            st.success("삭제되었습니다!")
                                            time.sleep(0.5)
                                        except:
                                            pass
                                    # 개수 조정
                                    if st.session_state[f'sell_date_count_{symbol}'] > 0:
                                        st.session_state[f'sell_date_count_{symbol}'] -= 1
                                    if st.session_state[f'sell_date_count_{symbol}'] == 0:
                                        st.session_state[f'sell_date_count_{symbol}'] = 1
                                    st.rerun()
                        
                        # 매도일 추가 버튼
                        if st.button("➕ 매도일 추가", key=f"add_sell_date_{symbol}"):
                            if st.session_state[f'sell_date_count_{symbol}'] < 10:
                                st.session_state[f'sell_date_count_{symbol}'] += 1
                                st.rerun()
                            else:
                                st.warning("최대 10개까지 추가 가능합니다.")
                        
                        edit_note = st.text_area(
                            "메모",
                            value=note if pd.notna(note) else "",
                            key=f"edit_note_{symbol}"
                        )
                        
                        edit_submitted = st.button("수정 저장", key="edit_submit_button")
                        
                        if edit_submitted:
                            df_stocks = load_stocks()
                            # Symbol 기준으로 해당 종목 찾아서 업데이트
                            mask = df_stocks['Symbol'] == symbol
                            if mask.any():
                                df_stocks.loc[mask, 'InterestDate'] = edit_interest_date.strftime("%Y-%m-%d") if edit_interest_date else ""
                                
                                # BuyTransactions 저장 (날짜만 있는 경우 기본값으로 저장)
                                buy_txs_to_save = []
                                for d in buy_date_inputs:
                                    if d is not None:
                                        buy_txs_to_save.append({
                                            "date": d.strftime("%Y-%m-%d"),
                                            "price": 0,
                                            "quantity": 0
                                        })
                                df_stocks.loc[mask, 'BuyTransactions'] = json.dumps(buy_txs_to_save) if buy_txs_to_save else "[]"
                                
                                # SellTransactions 저장 (날짜만 있는 경우 기본값으로 저장)
                                sell_txs_to_save = []
                                for d in sell_date_inputs:
                                    if d is not None:
                                        sell_txs_to_save.append({
                                            "date": d.strftime("%Y-%m-%d"),
                                            "price": 0,
                                            "quantity": 0
                                        })
                                df_stocks.loc[mask, 'SellTransactions'] = json.dumps(sell_txs_to_save) if sell_txs_to_save else "[]"
                                
                                df_stocks.loc[mask, 'Note'] = edit_note if edit_note else ""
                                save_stocks(df_stocks)
                                st.success("수정되었습니다!")
                                st.rerun()
                
                # 주가 데이터 가져오기
                with st.spinner(f"{name} ({symbol}) 데이터를 불러오는 중..."):
                    stock_data_full = get_stock_data(symbol)
                
                if stock_data_full is not None and not stock_data_full.empty:
                    # 기간선택 박스로 시작일/종료일 자동 설정
                    if selected_period and selected_period != "선택안함":
                        period_years = period_options[selected_period]
                        max_date = stock_data_full.index.max()
                        min_date = max_date - timedelta(days=int(period_years * 365))
                        # 기간선택 시 시작일/종료일 자동 계산
                        calculated_start_date = min_date.date()
                        calculated_end_date = max_date.date()
                    else:
                        calculated_start_date = start_date
                        calculated_end_date = end_date
                    
                    # 시작일/종료일에 맞춰 데이터 필터링
                    stock_data = stock_data_full.copy()
                    
                    # 기간선택이 있으면 계산된 날짜 사용, 없으면 사용자 입력 날짜 사용
                    filter_start_date = calculated_start_date if (selected_period and selected_period != "선택안함") else start_date
                    filter_end_date = calculated_end_date if (selected_period and selected_period != "선택안함") else end_date
                    
                    if filter_start_date is not None:
                        start_dt = pd.to_datetime(filter_start_date).normalize()
                        stock_data = stock_data[stock_data.index >= start_dt].copy()
                    
                    if filter_end_date is not None:
                        end_dt = pd.to_datetime(filter_end_date).normalize()
                        stock_data = stock_data[stock_data.index <= end_dt].copy()
                    
                    # 시작일/종료일이 모두 없으면 기본 5년
                    if filter_start_date is None and filter_end_date is None:
                        cutoff_date = stock_data_full.index.max() - timedelta(days=5 * 365)
                        stock_data = stock_data_full[stock_data_full.index >= cutoff_date].copy()
                    
                    # 캔들스틱 차트 생성
                    fig = go.Figure()
                    
                    # 캔들스틱 차트 추가 (한국 스타일 색상)
                    fig.add_trace(go.Candlestick(
                        x=stock_data.index,
                        open=stock_data['Open'],
                        high=stock_data['High'],
                        low=stock_data['Low'],
                        close=stock_data['Close'],
                        name="주가",
                        increasing=dict(
                            line=dict(color='#FF2E2E'),  # 상승: 빨강
                            fillcolor='#FF2E2E'
                        ),
                        decreasing=dict(
                            line=dict(color='#00C4FF'),  # 하락: 파랑
                            fillcolor='#00C4FF'
                        )
                    ))
                    
                    # 20주 이동평균선 및 80주 이동평균선 계산 및 추가
                    # 일봉 데이터를 주봉으로 변환 (주 단위로 리샘플링)
                    try:
                        # 주봉 데이터로 변환 (W-FRI: 금요일 기준 주봉)
                        weekly_data = stock_data.resample('W-FRI').agg({
                            'Open': 'first',
                            'High': 'max',
                            'Low': 'min',
                            'Close': 'last'
                        }).dropna()
                        
                        # 20주 이동평균 계산
                        if len(weekly_data) >= 20:
                            ma_20 = weekly_data['Close'].rolling(window=20).mean()
                            # 일봉 인덱스에 맞춰 보간 (interpolation)
                            ma_20_daily = ma_20.reindex(stock_data.index, method='ffill')
                            
                            fig.add_trace(go.Scatter(
                                x=stock_data.index,
                                y=ma_20_daily,
                                mode='lines',
                                name='20주 이동평균',
                                line=dict(color='#FF8C00', width=2),  # 주황색 (DarkOrange)
                                hovertemplate='20주 MA: %{y:.2f}<extra></extra>'
                            ))
                        
                        # 80주 이동평균 계산
                        if len(weekly_data) >= 80:
                            ma_80 = weekly_data['Close'].rolling(window=80).mean()
                            # 일봉 인덱스에 맞춰 보간 (interpolation)
                            ma_80_daily = ma_80.reindex(stock_data.index, method='ffill')
                            
                            fig.add_trace(go.Scatter(
                                x=stock_data.index,
                                y=ma_80_daily,
                                mode='lines',
                                name='80주 이동평균',
                                line=dict(color='#32CD32', width=2),  # 초록색 (LimeGreen)
                                hovertemplate='80주 MA: %{y:.2f}<extra></extra>'
                            ))
                    except Exception as e:
                        # 이동평균 계산 실패 시 무시 (차트는 정상 표시)
                        pass

                    
                    # 날짜별 주석 추가
                    annotations = []
                    sell_dates = []
                    sell_prices = []
                    
                    # 날짜 문자열을 datetime으로 변환하고 정규화하는 함수
                    def parse_date_safe(date_str):
                        if pd.isna(date_str) or date_str == "" or str(date_str).strip() == "":
                            return None
                        try:
                            # 문자열을 datetime으로 변환하고 날짜만 남기기 (시간 정보 제거)
                            date_dt = pd.to_datetime(date_str).normalize()
                            return date_dt
                        except Exception as e:
                            return None
                    
                    # 날짜에 해당하는 마커를 찾는 함수 (주말/휴장일이면 다음 거래일 사용)
                    def find_trading_date(target_date, data_index):
                        """
                        target_date에 해당하는 거래일을 찾습니다.
                        주말/휴장일이면 다음 거래일(bfill)을 반환합니다.
                        """
                        if len(data_index) == 0:
                            return None
                        
                        # 정규화된 날짜로 변환
                        target_date = pd.to_datetime(target_date).normalize()
                        
                        # 정확히 일치하는 날짜가 있는지 확인
                        if target_date in data_index:
                            return target_date
                        
                        # 정확히 일치하지 않으면 다음 거래일 찾기 (bfill)
                        # target_date 이후의 데이터만 필터링
                        future_dates = data_index[data_index >= target_date]
                        if len(future_dates) > 0:
                            # 다음 거래일 반환
                            return future_dates[0]
                        
                        # target_date 이전의 가장 가까운 날짜 찾기 (fallback)
                        past_dates = data_index[data_index <= target_date]
                        if len(past_dates) > 0:
                            return past_dates[-1]
                        
                        return None
                    
                    # 관심일 표시 (네온 노란색 화살표 - 아래 방향)
                    interest_dt = parse_date_safe(interest_date)
                    if interest_dt is not None:
                        try:
                            if len(stock_data.index) > 0:
                                # 거래일 찾기
                                trading_date = find_trading_date(interest_dt, stock_data.index)
                                if trading_date is not None and trading_date in stock_data.index:
                                    price = stock_data.loc[trading_date, 'High']
                                    # 가격 범위 계산 (텍스트 위치)
                                    price_range = stock_data['High'].max() - stock_data['Low'].min()
                                    offset = price_range * 0.01  # 가격 범위의 1%만큼 위로
                                    text_y = price + offset  # 텍스트 위치
                                    annotations.append(dict(
                                        x=trading_date,
                                        y=text_y,  # 텍스트는 위에
                                        xref="x",
                                        yref="y",
                                        text="👀 관심",
                                        showarrow=True,
                                        arrowhead=2,
                                        arrowcolor="#FFD700",  # 네온 노란색
                                        arrowsize=1.5,
                                        arrowwidth=2,
                                        ax=0,
                                        ay=-70,  # 고정값: 위로 70픽셀
                                        bgcolor="rgba(0, 0, 0, 0.5)",  # 반투명 검정 배경
                                        bordercolor="#FFD700",
                                        borderwidth=2,
                                        font=dict(size=14, color="#FFD700")  # 텍스트 크기 증가
                                    ))
                        except Exception as e:
                            pass
                    
                    # 매수일 표시 (네온 빨간색 화살표 - 위 방향) - BuyTransactions에서 날짜 추출
                    for idx, tx in enumerate(buy_transactions):
                        if isinstance(tx, dict):
                            buy_date_val = tx.get('date', '')
                        else:
                            buy_date_val = str(tx) if tx else ''
                        
                        if buy_date_val and str(buy_date_val).strip() != "":
                            buy_dt = parse_date_safe(buy_date_val)
                            if buy_dt is not None:
                                try:
                                    if len(stock_data.index) > 0:
                                        trading_date = find_trading_date(buy_dt, stock_data.index)
                                        if trading_date is not None and trading_date in stock_data.index:
                                            # 가격 정보가 있으면 사용, 없으면 Low 가격 사용
                                            tx_price = tx.get('price', 0) if isinstance(tx, dict) else 0
                                            if tx_price and tx_price > 0:
                                                price = tx_price
                                            else:
                                                price = stock_data.loc[trading_date, 'Low']
                                            
                                            # 가격 범위 계산 (텍스트 위치)
                                            price_range = stock_data['High'].max() - stock_data['Low'].min()
                                            offset = price_range * 0.01  # 가격 범위의 1%만큼 아래로
                                            text_y = price - offset  # 텍스트 위치
                                            text_label = "🔴 매수" if idx == 0 else f"🔴 매수{idx+1}"
                                            annotations.append(dict(
                                                x=trading_date,
                                                y=text_y,  # 텍스트는 아래에
                                                xref="x",
                                                yref="y",
                                                text=text_label,
                                                showarrow=True,
                                                arrowhead=2,
                                                arrowcolor="#FF2E2E",  # 네온 빨간색
                                                arrowsize=1.5,
                                                arrowwidth=2,
                                                ax=0,
                                                ay=70,  # 고정값: 아래로 70픽셀
                                                bgcolor="rgba(0, 0, 0, 0.5)",  # 반투명 검정 배경
                                                bordercolor="#FF2E2E",
                                                borderwidth=2,
                                                font=dict(size=14, color="#FF2E2E")  # 텍스트 크기 증가
                                            ))
                                except Exception as e:
                                    pass
                    
                    # 매도일 표시 (네온 하늘색 화살표 - 아래 방향) - SellTransactions에서 날짜 추출
                    for idx, tx in enumerate(sell_transactions):
                        if isinstance(tx, dict):
                            sell_date_val = tx.get('date', '')
                        else:
                            sell_date_val = str(tx) if tx else ''
                        
                        if sell_date_val and str(sell_date_val).strip() != "":
                            sell_dt = parse_date_safe(sell_date_val)
                            if sell_dt is not None:
                                try:
                                    if len(stock_data.index) > 0:
                                        trading_date = find_trading_date(sell_dt, stock_data.index)
                                        if trading_date is not None and trading_date in stock_data.index:
                                            # 가격 정보가 있으면 사용, 없으면 High 가격 사용
                                            tx_price = tx.get('price', 0) if isinstance(tx, dict) else 0
                                            if tx_price and tx_price > 0:
                                                price = tx_price
                                            else:
                                                price = stock_data.loc[trading_date, 'High']
                                            
                                            # 가격 범위 계산 (텍스트 위치)
                                            price_range = stock_data['High'].max() - stock_data['Low'].min()
                                            offset = price_range * 0.01  # 가격 범위의 1%만큼 위로
                                            text_y = price + offset  # 텍스트 위치
                                            sell_dates.append(trading_date)
                                            sell_prices.append(price)
                                            text_label = "🔵 매도" if idx == 0 else f"🔵 매도{idx+1}"
                                            annotations.append(dict(
                                                x=trading_date,
                                                y=text_y,  # 텍스트는 위에
                                                xref="x",
                                                yref="y",
                                                text=text_label,
                                                showarrow=True,  # 화살표 추가
                                                arrowhead=2,
                                                arrowcolor="#00C4FF",  # 네온 하늘색
                                                arrowsize=1.5,
                                                arrowwidth=2,
                                                ax=0,
                                                ay=-70,  # 고정값: 위로 70픽셀
                                                bgcolor="rgba(0, 0, 0, 0.5)",  # 반투명 검정 배경
                                                bordercolor="#00C4FF",
                                                borderwidth=2,
                                                font=dict(size=14, color="#00C4FF"),  # 텍스트 크기 증가
                                                yshift=10
                                            ))
                                except Exception as e:
                                    pass
                    
                    # 매도일 점 마커 추가 (네온 하늘색)
                    if sell_dates:
                        fig.add_trace(go.Scatter(
                            x=sell_dates,
                            y=sell_prices,
                            mode='markers',
                            marker=dict(
                                symbol='circle',
                                size=18,  # 크기 증가
                                color='#00C4FF',  # 네온 하늘색
                                line=dict(width=2, color='#0088CC')
                            ),
                            name="매도",
                            hovertemplate="매도일: %{x}<br>가격: %{y}<extra></extra>"
                        ))
                    
                    # 레이아웃 설정 (모던 핀테크 스타일)
                    fig.update_layout(
                        title=dict(
                            text=f"{name} ({symbol}) 주가 차트",
                            font=dict(size=20, color='#ffffff', family='Pretendard'),
                            x=0.5,
                            xanchor='center'
                        ),
                        xaxis=dict(
                            title=dict(
                                text="날짜",
                                font=dict(color='#e5e7eb', size=14, family='Pretendard')
                            ),
                            tickfont=dict(color='#9ca3af', size=12),
                            gridcolor='rgba(128, 128, 128, 0.1)',  # 연한 회색 그리드
                            gridwidth=1,
                            showgrid=True,
                            zeroline=False,
                            linecolor='rgba(255, 255, 255, 0.1)',
                            linewidth=1
                        ),
                        yaxis=dict(
                            title=dict(
                                text="가격",
                                font=dict(color='#e5e7eb', size=14, family='Pretendard')
                            ),
                            tickfont=dict(color='#9ca3af', size=12),
                            gridcolor='rgba(128, 128, 128, 0.1)',  # 연한 회색 그리드
                            gridwidth=1,
                            showgrid=True,
                            zeroline=False,
                            linecolor='rgba(255, 255, 255, 0.1)',
                            linewidth=1
                        ),
                        xaxis_rangeslider_visible=False,
                        height=600,
                        annotations=annotations,
                        hovermode='x unified',
                        dragmode='zoom',
                        plot_bgcolor='rgba(0, 0, 0, 0)',
                        paper_bgcolor='rgba(0, 0, 0, 0)',
                        font=dict(family='Pretendard', color='#e5e7eb'),
                        legend=dict(
                            bgcolor='rgba(0, 0, 0, 0)',
                            bordercolor='rgba(255, 255, 255, 0.1)',
                            borderwidth=1,
                            font=dict(color='#e5e7eb', size=12)
                        )
                    )
                    
                    # 차트 표시 (확대/축소 버튼 포함, 마우스 휠 줌 활성화)
                    st.plotly_chart(fig, use_container_width=True, config={
                        'modeBarButtonsToAdd': ['zoomIn2d', 'zoomOut2d', 'resetScale2d', 'pan2d'],
                        'displayModeBar': True,
                        'displaylogo': False,
                        'scrollZoom': True,  # 마우스 휠 줌 활성화
                        'toImageButtonOptions': {
                            'format': 'png',
                            'filename': f'{name}_{symbol}_chart',
                            'height': 600,
                            'width': 1200,
                            'scale': 1
                        }
                    })
                    
                    # 메모 표시
                    if pd.notna(note) and note != "":
                        st.info(f"**메모:** {note}")
                    else:
                        st.info("메모가 없습니다.")
                else:
                    st.error(f"{symbol} 종목의 데이터를 가져올 수 없습니다. 티커를 확인해주세요.")

# 탭 2: 분할 매수 플래너
with tab2:
    st.title("💰 주식 분할 매수 플래너")
    
    # 데이터 로드
    df_split = load_split_purchase_data()
    
    # 종목 상세 정보를 보여주는 Modal 함수
    @st.dialog("📊 종목 상세 관리")
    def show_stock_detail_modal(stock_id):
        """종목 상세 정보를 Modal Popup으로 표시"""
        # 최신 데이터 로드 (캐시 클리어하여 최신 데이터 가져오기)
        load_split_purchase_data.clear()
        df_split = load_split_purchase_data()
        
        # stock_id로 종목 찾기
        matching_rows = df_split[df_split['Symbol'] == stock_id]
        
        if matching_rows.empty:
            st.error("종목을 찾을 수 없습니다.")
            return
        
        stock_idx = matching_rows.index[0]
        stock_row = df_split.loc[stock_idx]
        
        stock_name = stock_row.get('Name', '')
        market_cap = stock_row.get('MarketCap', 0)
        installments = stock_row.get('Installments', 3)
        
        # BuyTransactions 파싱 (더 안전한 방식)
        buy_txs_raw = stock_row.get('BuyTransactions', '[]')
        buy_txs = []
        if pd.notna(buy_txs_raw) and str(buy_txs_raw).strip():
            if isinstance(buy_txs_raw, list):
                buy_txs = buy_txs_raw
            elif isinstance(buy_txs_raw, str):
                try:
                    buy_txs_str = str(buy_txs_raw).strip()
                    if buy_txs_str and buy_txs_str != '[]' and buy_txs_str != '':
                        buy_txs = json.loads(buy_txs_str)
                    else:
                        buy_txs = []
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    buy_txs = []
            else:
                buy_txs = []
        else:
            buy_txs = []
        
        # SellTransactions 파싱 (더 안전한 방식)
        sell_txs_raw = stock_row.get('SellTransactions', '[]')
        sell_txs = []
        if pd.notna(sell_txs_raw) and str(sell_txs_raw).strip():
            if isinstance(sell_txs_raw, list):
                sell_txs = sell_txs_raw
            elif isinstance(sell_txs_raw, str):
                try:
                    sell_txs_str = str(sell_txs_raw).strip()
                    if sell_txs_str and sell_txs_str != '[]' and sell_txs_str != '':
                        sell_txs = json.loads(sell_txs_str)
                    else:
                        sell_txs = []
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    sell_txs = []
            else:
                sell_txs = []
        else:
            sell_txs = []
        
        # MarketCap을 안전하게 숫자로 변환
        try:
            if pd.notna(market_cap) and str(market_cap).strip() != "":
                market_cap_value = float(market_cap)
            else:
                market_cap_value = 0
        except (ValueError, TypeError):
            market_cap_value = 0
        
        max_investment = market_cap_value / 10000
        amount_per_installment = max_investment / installments if installments > 0 else 0
        
        # === 이동평균법(Moving Average Cost) 계산 로직 ===
        # 1. 데이터 통합 및 정렬
        all_transactions = []
        
        # 매수 거래 추가
        for tx in buy_txs:
            if isinstance(tx, dict) and tx.get('date') and tx.get('price') and tx.get('quantity'):
                try:
                    tx_date = pd.to_datetime(tx.get('date')).date()
                    all_transactions.append({
                        'type': 'buy',
                        'date': tx_date,
                        'price': float(tx.get('price', 0)),
                        'quantity': int(tx.get('quantity', 0)),
                        'original_tx': tx
                    })
                except:
                    pass
        
        # 매도 거래 추가
        for tx in sell_txs:
            if isinstance(tx, dict) and tx.get('date') and tx.get('price') and tx.get('quantity'):
                try:
                    tx_date = pd.to_datetime(tx.get('date')).date()
                    all_transactions.append({
                        'type': 'sell',
                        'date': tx_date,
                        'price': float(tx.get('price', 0)),
                        'quantity': int(tx.get('quantity', 0)),
                        'original_tx': tx
                    })
                except:
                    pass
        
        # 날짜 순으로 정렬 (날짜가 같으면 매수가 먼저)
        all_transactions.sort(key=lambda x: (x['date'], 0 if x['type'] == 'buy' else 1))
        
        # 2. 순차적 계산 루프
        current_qty = 0
        current_avg_price = 0.0
        total_realized_profit = 0.0
        
        for tx in all_transactions:
            if tx['type'] == 'buy':
                # 매수 발생 시: 평단가 갱신
                buy_price = tx['price']
                buy_qty = tx['quantity']
                
                if current_qty == 0:
                    # 첫 매수
                    current_avg_price = buy_price
                    current_qty = buy_qty
                else:
                    # 추가 매수: 이동평균 계산
                    total_cost_before = current_qty * current_avg_price
                    total_cost_new = buy_qty * buy_price
                    current_qty += buy_qty
                    current_avg_price = (total_cost_before + total_cost_new) / current_qty
                    
            elif tx['type'] == 'sell':
                # 매도 발생 시: 실현손익 계산 (현재 시점의 평단가 기준)
                sell_price = tx['price']
                sell_qty = tx['quantity']
                
                if current_avg_price > 0:
                    # 실현손익 계산
                    realized_profit = (sell_price - current_avg_price) * sell_qty
                    yield_pct = ((sell_price - current_avg_price) / current_avg_price * 100) if current_avg_price > 0 else 0
                    
                    # 매도 거래 객체에 계산된 값 저장
                    tx['original_tx']['realized_profit'] = realized_profit
                    tx['original_tx']['yield_pct'] = yield_pct
                    
                    total_realized_profit += realized_profit
                
                # 수량 감소 (평단가는 변하지 않음)
                current_qty -= sell_qty
                if current_qty < 0:
                    current_qty = 0
        
        # 3. 결과 적용
        avg_price = current_avg_price  # 현재 보유 물량에 대한 평단가
        current_invested = current_qty * avg_price
        progress = (current_invested / max_investment * 100) if max_investment > 0 else 0
        
        # 종목명 표시
        st.subheader(f"{stock_name}")
            
        # 요약 정보
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("최대 매수 가능액", f"{max_investment:,.0f}원")
        col2.metric("총 매입금액", f"{current_invested:,.0f}원")
        col3.metric("매입 평단가", f"{avg_price:,.0f}원")
        col4.metric("보유 수량", f"{current_qty:,} 주")
        
        # 분할 횟수 수정 가능하게
        with col5:
                st.write("**분할 횟수**")
                col5_1, col5_2 = st.columns([2, 1])
                with col5_1:
                    st.write(f"{installments}회")
                with col5_2:
                    new_installments = st.number_input(
                        "수정",
                        min_value=1,
                        value=installments,
                        step=1,
                        key=f"edit_installments_{stock_id}",
                        label_visibility="collapsed"
                    )
                if new_installments != installments:
                    if st.button("적용", key=f"apply_installments_{stock_id}", type="secondary", use_container_width=True):
                        df_split.at[stock_idx, 'Installments'] = int(new_installments)
                        save_split_purchase_data(df_split)
                        st.success("분할 횟수가 수정되었습니다!")
                        st.rerun()
            
        # 진행률
        progress_value = max(0.0, min(1.0, progress / 100))
        st.progress(progress_value)
        col_prog1, col_prog2 = st.columns(2)
        col_prog1.write(f"**매수 진행률: {progress:.2f}%**")
        col_prog2.write(f"**총 실현손익: {total_realized_profit:,.0f}원**")
        
        st.divider()
        
        # 매수 계획 및 기록
        col_buy, col_sell = st.columns(2)
        
        with col_buy:
                st.subheader("매수 계획 및 기록")
                
                # 테이블 헤더
                st.markdown("""
                <div style="
                    background: rgba(99, 102, 241, 0.2);
                    border-radius: 8px;
                    padding: 0.8rem;
                    margin-bottom: 0.5rem;
                    border: 1px solid rgba(99, 102, 241, 0.3);
                ">
                <div style="display: flex; justify-content: space-between; align-items: center; font-weight: 600;">
                    <div style="flex: 0.5; text-align: center;">회차</div>
                    <div style="flex: 1.2; text-align: center;">날짜</div>
                    <div style="flex: 1.3; text-align: center;">목표액</div>
                    <div style="flex: 1.5; text-align: center;">매수가</div>
                    <div style="flex: 1.1; text-align: center;">매수량</div>
                    <div style="flex: 0.7; text-align: center;">실행</div>
                </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 각 회차별로 개별 입력 폼 생성
                for i in range(installments):
                    tx = buy_txs[i] if i < len(buy_txs) else None
                    
                    # 기존 데이터 불러오기
                    existing_date = None
                    existing_price = 0.0
                    existing_qty = 0
                    
                    if tx and isinstance(tx, dict):
                        if tx.get('date'):
                            try:
                                existing_date = pd.to_datetime(tx.get('date')).date()
                            except:
                                existing_date = datetime.now().date()
                        existing_price = float(tx.get('price', 0)) if tx.get('price') else 0.0
                        existing_qty = int(tx.get('quantity', 0)) if tx.get('quantity') else 0
                    
                    # 카드 형태로 각 행 표시
                    st.markdown(f"""
                    <div style="
                        background: rgba(255, 255, 255, 0.05);
                        border-radius: 8px;
                        padding: 0.5rem 1rem;
                        margin-bottom: 0;
                        border: 1px solid rgba(255, 255, 255, 0.1);
                    ">
                    """, unsafe_allow_html=True)
                    
                    # 각 행을 st.form으로 감싸서 리로드 방지
                    with st.form(f"buy_form_{stock_id}_{i}", clear_on_submit=False):
                        # 행 레이아웃: 회차 | 날짜 | 목표액 | 매수가 | 매수량 | 실행
                        col_round, col_date, col_target, col_price, col_qty, col_action = st.columns([0.5, 1.2, 1.3, 1.5, 1.1, 0.7])
                        
                        with col_round:
                            st.markdown(f"<div style='text-align: center; font-size: 1rem; font-weight: 600;'>{i+1}</div>", unsafe_allow_html=True)
                        
                        with col_date:
                            buy_date = st.date_input(
                                "날짜",
                                value=existing_date if existing_date else datetime.now().date(),
                                key=f"buy_date_{stock_id}_{i}",
                                label_visibility="collapsed"
                            )
                        
                        with col_target:
                            st.markdown(f"<div style='text-align: center; color: #9ca3af;'>₩{amount_per_installment:,.0f}</div>", unsafe_allow_html=True)
                            
                        with col_price:
                            buy_price = st.number_input(
                                "매수가",
                                min_value=0,
                                value=int(existing_price) if existing_price > 0 else None,
                                step=100,
                                key=f"buy_price_{stock_id}_{i}",
                                label_visibility="collapsed",
                                placeholder="가격",
                                format="%d"
                            )
                        
                        with col_qty:
                            buy_qty = st.number_input(
                                "매수량",
                                min_value=0,
                                value=existing_qty if existing_qty > 0 else None,
                                step=1,
                                key=f"buy_qty_{stock_id}_{i}",
                                label_visibility="collapsed",
                                placeholder="수량"
                            )
                        
                        with col_action:
                            # 수정/기록 버튼
                            if existing_date or existing_price > 0 or existing_qty > 0:
                                button_label = "수정"
                                button_type = "secondary"  # 수정 버튼은 파란색
                            else:
                                button_label = "기록"
                                button_type = "primary"  # 기록 버튼은 빨간색
                            
                            if st.form_submit_button(button_label, type=button_type, use_container_width=True):
                                # buy_txs 리스트 확장
                                while len(buy_txs) < installments:
                                    buy_txs.append(None)
                                
                                # 데이터 저장
                                if buy_date and buy_price is not None and buy_price > 0 and buy_qty is not None and buy_qty > 0:
                                    buy_txs[i] = {
                                        'date': str(buy_date),
                                        'price': int(buy_price),
                                        'quantity': int(buy_qty)
                                    }
                                    
                                    # 구글 스프레드시트에 저장
                                    df_split.at[stock_idx, 'BuyTransactions'] = json.dumps(buy_txs)
                                    save_split_purchase_data(df_split)
                                    st.success(f"회차 {i+1} 매수 기록이 저장되었습니다!")
                                    st.rerun()
                                else:
                                    st.warning("날짜, 매수가, 매수량을 모두 입력해주세요.")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
            
        with col_sell:
            st.subheader("분할 매도 기록")
            
            # 매도 기록 추가 입력
            st.caption(f"{stock_name} 매도 기록 추가")
            with st.form(f"sell_form_{stock_id}", clear_on_submit=True):
                col_sell_input1, col_sell_input2, col_sell_input3, col_sell_input4 = st.columns([2, 2, 2, 1], vertical_alignment="bottom")
                
                with col_sell_input1:
                    sell_date = st.date_input("날짜", datetime.now(), key=f"sell_date_{stock_id}", label_visibility="collapsed")
                with col_sell_input2:
                    sell_price = st.number_input("매도가 (원)", min_value=0, step=100, value=None, key=f"sell_price_{stock_id}", label_visibility="collapsed", placeholder="매도 가격")
                with col_sell_input3:
                    sell_qty = st.number_input("매도 수량 (주)", min_value=1, step=1, value=None, key=f"sell_qty_{stock_id}", label_visibility="collapsed", placeholder="매도 수량")
                with col_sell_input4:
                    if st.form_submit_button("추가", type="primary", use_container_width=True):
                        if sell_price is None or sell_qty is None:
                            st.warning("매도가와 매도 수량을 입력해주세요.")
                        else:
                            new_sell = {
                                'id': f"{datetime.now().timestamp()}",
                                'date': str(sell_date),
                                'price': float(sell_price),
                                'quantity': int(sell_qty)
                            }
                            sell_txs.append(new_sell)
                            df_split.at[stock_idx, 'SellTransactions'] = json.dumps(sell_txs)
                            save_split_purchase_data(df_split)
                            st.success("매도 기록이 저장되었습니다!")
                            st.rerun()
            
            st.divider()
            
            # 매도 기록 테이블
            if sell_txs:
                # 테이블 헤더
                st.markdown("""
                <div style="
                    background: rgba(99, 102, 241, 0.2);
                    border-radius: 8px;
                    padding: 0.5rem 0.8rem;
                    margin-bottom: 0.2rem;
                    border: 1px solid rgba(99, 102, 241, 0.3);
                ">
                <div style="display: flex; justify-content: space-between; align-items: center; font-weight: 600;">
                    <div style="flex: 0.5; text-align: center;">회차</div>
                    <div style="flex: 1.2; text-align: center;">날짜</div>
                    <div style="flex: 1.2; text-align: center;">매도가</div>
                    <div style="flex: 1.2; text-align: center;">수량</div>
                    <div style="flex: 1.0; text-align: center;">수익률</div>
                    <div style="flex: 1.2; text-align: center;">수익금</div>
                    <div style="flex: 0.8; text-align: center;">실행</div>
                </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 각 매도 기록을 카드 형태로 표시
                for i, tx in enumerate(sell_txs):
                    if isinstance(tx, dict):
                        # 이동평균법으로 계산된 값 사용 (없으면 0)
                        profit = tx.get('realized_profit', 0)
                        yield_pct = tx.get('yield_pct', 0)
                        
                        # 날짜 파싱
                        tx_date = None
                        if tx.get('date'):
                            try:
                                tx_date = pd.to_datetime(tx.get('date')).date()
                            except:
                                tx_date = datetime.now().date()
                        
                        # 카드 형태로 각 행 표시
                        st.markdown(f"""
                        <div style="
                            background: rgba(255, 255, 255, 0.05);
                            border-radius: 8px;
                            padding: 0.5rem 1rem;
                            margin-bottom: 0;
                            border: 1px solid rgba(255, 255, 255, 0.1);
                        ">
                        """, unsafe_allow_html=True)
                        
                        # 행 레이아웃: 회차 | 날짜 | 매도가 | 수량 | 수익률 | 수익금 | 실행
                        col_round, col_date, col_price, col_qty, col_yield, col_profit, col_action = st.columns([0.5, 1.2, 1.2, 1.2, 1.0, 1.2, 0.8])
                        
                        with col_round:
                            st.markdown(f"<div style='text-align: center; font-size: 1rem; font-weight: 600;'>{i+1}</div>", unsafe_allow_html=True)
                        
                        with col_date:
                            st.markdown(f"<div style='text-align: center;'>{tx_date.strftime('%Y-%m-%d') if tx_date else tx.get('date', '')}</div>", unsafe_allow_html=True)
                        
                        with col_price:
                            st.markdown(f"<div style='text-align: center;'>{tx.get('price', 0):,.0f}</div>", unsafe_allow_html=True)
                        
                        with col_qty:
                            st.markdown(f"<div style='text-align: center;'>{tx.get('quantity', 0):,}</div>", unsafe_allow_html=True)
                        
                        with col_yield:
                            yield_color = "#ef4444" if yield_pct < 0 else "#10b981"
                            st.markdown(f"<div style='text-align: center; color: {yield_color}; font-weight: 600;'>{yield_pct:.2f}%</div>", unsafe_allow_html=True)
                        
                        with col_profit:
                            profit_color = "#ef4444" if profit < 0 else "#10b981"
                            st.markdown(f"<div style='text-align: center; color: {profit_color}; font-weight: 600;'>{profit:,.0f}</div>", unsafe_allow_html=True)
                        
                        with col_action:
                            if st.button("삭제", key=f"delete_sell_{stock_id}_{i}", type="primary", use_container_width=True):
                                sell_txs.pop(i)
                                df_split.at[stock_idx, 'SellTransactions'] = json.dumps(sell_txs)
                                save_split_purchase_data(df_split)
                                st.success("매도 기록이 삭제되었습니다!")
                                st.rerun()
                        
                        st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("매도 기록이 없습니다.")
        
        # 종목 삭제 버튼
        st.divider()
        if st.button(f"🗑️ {stock_name} 삭제", key=f"delete_stock_{stock_id}", type="secondary"):
            df_split = df_split.drop(stock_idx).reset_index(drop=True)
            save_split_purchase_data(df_split)
            st.success(f"{stock_name} 종목이 삭제되었습니다!")
            st.rerun()
    
    # Installments가 있는 종목만 필터링 (분할 매수 플래너용)
    if not df_split.empty:
        # Installments가 비어있지 않은 종목만 (숫자 또는 문자열 모두 처리)
        def has_installments(val):
            if pd.isna(val):
                return False
            if val == '' or val == 0:
                return False
            try:
                # 숫자로 변환 가능한지 확인
                float_val = float(val)
                return float_val > 0
            except (ValueError, TypeError):
                return False
        
        df_split = df_split[df_split['Installments'].apply(has_installments)].copy()
        
        # JSON 파싱 (필터링 후)
        if 'BuyTransactions' in df_split.columns:
            df_split['BuyTransactions'] = df_split['BuyTransactions'].apply(
                lambda x: json.loads(x) if isinstance(x, str) and x and x != '[]' else []
            )
        if 'SellTransactions' in df_split.columns:
            df_split['SellTransactions'] = df_split['SellTransactions'].apply(
                lambda x: json.loads(x) if isinstance(x, str) and x and x != '[]' else []
            )
    
    # ==========================================
    # 1. 포트폴리오 요약 및 우측 상단 버튼
    # ==========================================
    col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
    with col_header1:
        st.subheader("📊 포트폴리오 요약")
        
        # 총 예산과 진행률을 위한 placeholder (초록색 박스 1, 2)
        col_summary_left1, col_summary_left2 = st.columns(2)
        with col_summary_left1:
            # 총 예산 placeholder (박스 1)
            st.session_state['budget_placeholder'] = st.empty()
        with col_summary_left2:
            # 진행률 placeholder (박스 2)
            st.session_state['progress_placeholder'] = st.empty()
    
    with col_header2:
        # 투자전략 필터 (분할매수 플래너)
        if not df_split.empty:
            # 세션 상태 초기화
            if 'split_strategy_filter' not in st.session_state:
                st.session_state['split_strategy_filter'] = "전체"
            
            strategy_filter = st.selectbox(
                "투자전략 필터",
                options=["전체", "Long", "Short", "Macro"],
                index=0,
                key="split_strategy_filter"
            )
            
            # 투자전략 필터링 적용
            if strategy_filter != "전체":
                df_split = df_split[df_split['Category'].astype(str).str.strip() == strategy_filter].copy()
    
    with col_header3:
        # 우측 상단 버튼 영역
        st.markdown("<br>", unsafe_allow_html=True)  # 여백
        with st.expander("➕ 새 종목 추가", expanded=False):
            with st.form("add_split_stock_form"):
                symbol = st.text_input("티커 (예: AAPL, 005930.KS)", placeholder="예: 005930.KS", key="split_symbol_input")
                name = st.text_input("종목명", placeholder="예: 삼성전자", key="split_name_input")
                interest_date = st.date_input("관심일", value=None, key="split_interest_date_input")
                market_cap = st.number_input("시가총액 (억원)", min_value=0, step=1000, placeholder="예: 5000000", key="split_market_cap_input")
                installments = st.number_input("분할 횟수", min_value=1, value=3, key="split_installments_input")
                category = st.selectbox("투자 전략", options=["Long", "Short", "Macro"], key="split_category_input")
                
                if st.form_submit_button("계획 추가"):
                    if name and market_cap > 0:
                        # Symbol 중복 체크
                        symbol_normalized = symbol.strip().upper() if symbol else ""
                        all_stocks = load_stocks()
                        
                        if symbol_normalized:
                            existing_symbols = all_stocks['Symbol'].astype(str).str.strip().str.upper()
                            if symbol_normalized in existing_symbols.values:
                                st.error("이미 등록된 티커입니다.")
                            else:
                                # 새 종목 추가
                                new_row = {
                                    "Symbol": symbol_normalized,
                                    "Name": name,
                                    "InterestDate": interest_date.strftime("%Y-%m-%d") if interest_date else "",
                                    "Note": "",
                                    "MarketCap": market_cap * 100000000,  # 억원을 원으로 변환
                                    "Installments": int(installments),
                                    "Category": category,
                                    "BuyTransactions": json.dumps([]),
                                    "SellTransactions": json.dumps([])
                                }
                                df_split = pd.concat([df_split, pd.DataFrame([new_row])], ignore_index=True)
                                save_split_purchase_data(df_split)
                                st.success(f"{name} 종목이 추가되었습니다!")
                                st.rerun()
                        else:
                            st.error("티커를 입력해주세요.")
                    else:
                        st.error("종목명과 시가총액을 입력해주세요.")
        
        with st.expander("📋 관심종목에서 가져오기", expanded=False):
            all_stocks = load_stocks()
            
            # 관심종목 필터링 (Installments가 비어있고 BuyTransactions가 비어있는 종목)
            interest_stocks = []
            for idx, row in all_stocks.iterrows():
                installments = row.get('Installments', '')
                buy_txs_str = row.get('BuyTransactions', '[]')
                
                # Installments가 비어있고 BuyTransactions가 비어있는 종목
                has_installments = pd.notna(installments) and str(installments).strip() != "" and installments != 0
                has_buy = False
                try:
                    if pd.notna(buy_txs_str) and str(buy_txs_str).strip() and buy_txs_str != '[]':
                        buy_txs = json.loads(buy_txs_str) if isinstance(buy_txs_str, str) else buy_txs_str
                        has_buy = len(buy_txs) > 0 if isinstance(buy_txs, list) else False
                except:
                    pass
                
                if not has_installments and not has_buy:
                    interest_stocks.append({
                        'Symbol': row.get('Symbol', ''),
                        'Name': row.get('Name', ''),
                        'InterestDate': row.get('InterestDate', '')
                    })
            
            if interest_stocks:
                # 가나다 순으로 정렬 (종목명 기준)
                interest_stocks_sorted = sorted(interest_stocks, key=lambda x: x['Name'])
                interest_options = [f"{s['Name']} ({s['Symbol']})" for s in interest_stocks_sorted]
                selected_interest = st.selectbox("관심종목 선택", interest_options, key="select_interest_stock")
                
                with st.form("import_interest_stock_form"):
                    # 선택된 종목 정보 표시
                    selected_idx = interest_options.index(selected_interest) if selected_interest in interest_options else -1
                    if selected_idx >= 0:
                        selected_stock = interest_stocks_sorted[selected_idx]
                        st.info(f"선택된 종목: {selected_stock['Name']} ({selected_stock['Symbol']})")
                    
                    market_cap = st.number_input("시가총액 (억원)", min_value=0, step=1000, placeholder="예: 5000000", key="import_market_cap")
                    installments = st.number_input("분할 횟수", min_value=1, value=3, key="import_installments")
                    category = st.selectbox("투자 전략", options=["Long", "Short", "Macro"], key="import_category")
                    
                    if st.form_submit_button("분할 매수 플래너에 추가"):
                        if selected_idx >= 0 and market_cap > 0:
                            selected_stock = interest_stocks_sorted[selected_idx]
                            # 기존 종목 업데이트
                            all_stocks = load_stocks()
                            mask = all_stocks['Symbol'] == selected_stock['Symbol']
                            if mask.any():
                                all_stocks.loc[mask, 'MarketCap'] = market_cap * 100000000
                                all_stocks.loc[mask, 'Installments'] = int(installments)
                                all_stocks.loc[mask, 'Category'] = category
                                save_stocks(all_stocks)
                                st.success(f"{selected_stock['Name']}이(가) 분할 매수 플래너에 추가되었습니다!")
                                st.rerun()
                        else:
                            st.error("시가총액을 입력해주세요.")
            else:
                st.info("관심종목이 없습니다.")
    
    if df_split.empty:
        st.info("추가된 종목이 없습니다.")
    else:
        # 포트폴리오 계산
        portfolio_data = []
        total_invested = 0
        total_budget = 0
        
        for _, stock in df_split.iterrows():
            buy_txs = stock.get('BuyTransactions', []) if isinstance(stock.get('BuyTransactions'), list) else []
            sell_txs = stock.get('SellTransactions', []) if isinstance(stock.get('SellTransactions'), list) else []
            
            # 매수 총액 계산
            buy_cost = 0
            buy_qty = 0
            for tx in buy_txs:
                if tx and isinstance(tx, dict):
                    buy_cost += tx.get('price', 0) * tx.get('quantity', 0)
                    buy_qty += tx.get('quantity', 0)
            
            # 매도 수량 계산
            sell_qty = sum(tx.get('quantity', 0) for tx in sell_txs if isinstance(tx, dict))
            
            avg_price = buy_cost / buy_qty if buy_qty > 0 else 0
            current_qty = buy_qty - sell_qty
            current_invested = current_qty * avg_price
            
            # MarketCap을 안전하게 숫자로 변환
            market_cap_value = stock.get('MarketCap', 0)
            try:
                if pd.notna(market_cap_value) and str(market_cap_value).strip() != "":
                    market_cap_value = float(market_cap_value)
                else:
                    market_cap_value = 0
            except (ValueError, TypeError):
                market_cap_value = 0
            
            max_investment = market_cap_value / 10000
            progress = (current_invested / max_investment * 100) if max_investment > 0 else 0
            
            portfolio_data.append({
                'id': stock.get('Symbol', f'stock_{idx}'),  # Symbol을 ID로 사용
                'name': stock.get('Name', ''),
                'totalInvested': current_invested,
                'progress': progress,
                'maxInvestment': max_investment
            })
            
            total_invested += current_invested
            total_budget += max_investment
        
        overall_progress = (total_invested / total_budget * 100) if total_budget > 0 else 0
        
        # 총 예산과 진행률을 왼쪽 초록색 박스(1, 2)에 표시 (보라색 배경)
        # 총 예산 (박스 1)
        if 'budget_placeholder' in st.session_state:
            st.session_state['budget_placeholder'].markdown(f"""
            <div style="
                background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                border: 2px solid #10b981;
                border-radius: 10px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 4px 6px rgba(99, 102, 241, 0.3);
                min-height: 100px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="color: rgba(255, 255, 255, 0.9); font-size: 0.9rem; margin-bottom: 0.5rem;">총 예산</div>
                <div style="color: #ffffff; font-size: 1.8rem; font-weight: 700;">₩{total_budget:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 진행률 (박스 2)
        if 'progress_placeholder' in st.session_state:
            st.session_state['progress_placeholder'].markdown(f"""
            <div style="
                background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                border: 2px solid #10b981;
                border-radius: 10px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 4px 6px rgba(99, 102, 241, 0.3);
                min-height: 100px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="color: rgba(255, 255, 255, 0.9); font-size: 0.9rem; margin-bottom: 0.5rem;">진행률</div>
                <div style="color: #ffffff; font-size: 1.8rem; font-weight: 700;">{overall_progress:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 도넛 차트 (개선된 버전)
        if total_invested > 0:
            colors = px.colors.qualitative.Plotly
            chart_df = pd.DataFrame(portfolio_data)
            chart_df = chart_df[chart_df['totalInvested'] > 0].sort_values('totalInvested', ascending=False)
            
            if not chart_df.empty:
                # 종목 수에 따라 차트 높이 동적 조정
                num_stocks = len(chart_df)
                # 기본 500, 종목이 많을수록 높이 증가 (최대 800)
                chart_height = min(500 + (num_stocks - 5) * 20, 800) if num_stocks > 5 else 500
                
                # 작은 비중 종목들을 "기타"로 묶기 (1% 미만)
                threshold = total_invested * 0.01  # 1% 기준
                main_stocks = chart_df[chart_df['totalInvested'] >= threshold]
                other_stocks = chart_df[chart_df['totalInvested'] < threshold]
                
                if len(other_stocks) > 0 and len(main_stocks) > 0:
                    # "기타" 항목 생성
                    other_total = other_stocks['totalInvested'].sum()
                    other_row = pd.DataFrame([{
                        'name': f'기타 ({len(other_stocks)}개)',
                        'totalInvested': other_total
                    }])
                    chart_df = pd.concat([main_stocks, other_row], ignore_index=True)
                
                fig_donut = px.pie(
                    chart_df,
                    values='totalInvested',
                    names='name',
                    hole=0.6,
                    color_discrete_sequence=colors
                )
                
                # 텍스트 표시 방식 조정: 일정 비율 이상만 표시
                # 종목 수가 많으면 label만 표시, 적으면 label+percent
                if num_stocks > 15:
                    textinfo = 'label'  # 종목이 많으면 라벨만
                else:
                    textinfo = 'label+percent'  # 종목이 적으면 라벨+퍼센트
                
                # 중앙에 총 매입금액 표시
                fig_donut.update_traces(
                    textposition='outside',
                    textinfo=textinfo,
                    hovertemplate='<b>%{label}</b><br>매입금액: ₩%{value:,.0f}<br>비중: %{percent}<extra></extra>',
                    textfont=dict(size=10 if num_stocks > 15 else 12)  # 종목이 많으면 폰트 크기 줄임
                )
                
                fig_donut.update_layout(
                    title=dict(
                        text="포트폴리오 요약",
                        font=dict(size=24, color='#a78bfa', family='Pretendard'),
                        x=0.5,
                        xanchor='center'
                    ),
                    annotations=[
                        dict(
                            text=f'<b>전체 총 매입금액</b><br>₩{total_invested:,.0f}',
                            x=0.5,
                            y=0.5,
                            font_size=20,
                            font_color='#ffffff',
                            showarrow=False,
                            font_family='Pretendard'
                        )
                    ],
                    showlegend=True,
                    legend=dict(
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.05,
                        font=dict(color='#ffffff', size=10 if num_stocks > 20 else 12, family='Pretendard')  # 범례 폰트도 조정
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#ffffff', family='Pretendard'),
                    height=chart_height,  # 동적 높이 사용
                    margin=dict(l=0, r=150, t=80, b=0)
                )
                st.plotly_chart(fig_donut, use_container_width=True)
        
        # 매수종목 뱃지 (그라데이션으로 진행률 표시)
        if portfolio_data:
            st.markdown("### 종목별 현황")
            
            # 오버레이 뱃지 생성 함수
            def create_overlay_badge(name, progress, key):
                """CSS 오버레이 기법으로 뱃지 생성 (JavaScript 동적 처리)"""
                progress_pct = min(100, max(0, progress))
                dark_green = '#10b981'
                light_green = '#86efac'
                gradient = f'linear-gradient(to right, {dark_green} 0%, {dark_green} {progress_pct}%, {light_green} {progress_pct}%, {light_green} 100%)'
                
                # 고유 ID 생성
                unique_id = f"badge-{key.replace('_', '-')}"
                # JavaScript에서 사용할 텍스트 (특수문자 이스케이프)
                badge_text_escaped = name.replace("'", "\\'").replace('"', '\\"')
                
                # HTML과 CSS + JavaScript 통합 렌더링
                st.markdown(f"""
                <div id="{unique_id}" class="badge-overlay-visual" style="
                    background: {gradient};
                    border: 2px solid {dark_green};
                    border-radius: 12px;
                    color: #ffffff;
                    font-weight: 600;
                    font-size: 0.95rem;
                    padding: 0.8rem 1.5rem;
                    min-height: 48px;
                    text-align: center;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-family: 'Pretendard', sans-serif;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    transition: all 0.3s ease;
                    margin-bottom: 0;
                    position: relative;
                    z-index: 1;
                    user-select: none;
                    pointer-events: none;
                ">{name}</div>
                <script>
                    (function() {{
                        const badgeId = '{unique_id}';
                        const badgeText = '{badge_text_escaped}';
                        
                        function hideButton() {{
                            // 뱃지 요소 찾기
                            const badge = document.getElementById(badgeId);
                            if (!badge) return;
                            
                            // 뱃지의 부모 컨테이너 찾기
                            let container = badge.closest('[data-testid="stElementContainer"]') || 
                                           badge.closest('[data-testid="stVerticalBlock"]') ||
                                           badge.closest('[data-testid="column"]');
                            
                            if (!container) return;
                            
                            // 컨테이너 다음에 오는 모든 형제 요소 탐색
                            let sibling = container.nextElementSibling;
                            let found = false;
                            
                            // 최대 5개 형제까지 탐색 (안전장치)
                            for (let i = 0; i < 5 && sibling; i++) {{
                                // stButton 컨테이너 찾기
                                const buttonContainer = sibling.querySelector('[data-testid="stButton"]');
                                if (buttonContainer) {{
                                    const button = buttonContainer.querySelector('button');
                                    if (button) {{
                                        // 버튼 텍스트 확인 (정확한 매칭)
                                        const buttonText = button.textContent.trim() || 
                                                         button.querySelector('p')?.textContent.trim() || 
                                                         button.querySelector('span')?.textContent.trim() || '';
                                        
                                        if (buttonText === badgeText || buttonText.includes(badgeText) || badgeText.includes(buttonText)) {{
                                            // 버튼 스타일 적용
                                            button.style.cssText = 'opacity: 0 !important; background: transparent !important; border: none !important; color: transparent !important; width: 100% !important; height: 53px !important; min-height: 53px !important; padding: 0 !important; margin: 0 !important; margin-top: -53px !important; cursor: pointer !important; position: relative !important; z-index: 99 !important; pointer-events: auto !important;';
                                            
                                            // 버튼 컨테이너도 조정
                                            buttonContainer.style.cssText = 'margin-top: -53px !important; position: relative !important; z-index: 99 !important;';
                                            
                                            // 호버/포커스/액티브 상태도 처리
                                            button.addEventListener('mouseenter', function(e) {{
                                                e.target.style.background = 'transparent';
                                                e.target.style.border = 'none';
                                            }});
                                            button.addEventListener('focus', function(e) {{
                                                e.target.style.background = 'transparent';
                                                e.target.style.border = 'none';
                                                e.target.style.color = 'transparent';
                                            }});
                                            button.addEventListener('mousedown', function(e) {{
                                                e.target.style.background = 'transparent';
                                                e.target.style.border = 'none';
                                                e.target.style.color = 'transparent';
                                            }});
                                            
                                            found = true;
                                            break;
                                        }}
                                    }}
                                }}
                                sibling = sibling.nextElementSibling;
                            }}
                        }}
                        
                        // DOM 로드 후 실행
                        if (document.readyState === 'loading') {{
                            document.addEventListener('DOMContentLoaded', hideButton);
                        }} else {{
                            hideButton();
                        }}
                        
                        // MutationObserver로 동적 추가 감지
                        const observer = new MutationObserver(hideButton);
                        observer.observe(document.body, {{
                            childList: true,
                            subtree: true
                        }});
                        
                        // 짧은 지연 후 재시도 (Streamlit 렌더링 대기)
                        setTimeout(hideButton, 100);
                        setTimeout(hideButton, 500);
                    }})();
                </script>
                """, unsafe_allow_html=True)
                
                # 투명 버튼 생성
                if st.button(name, key=key, use_container_width=True):
                    return True
                return False
            
            # 뱃지들을 그리드로 표시 (CSS 오버레이 기법)
            # 가나다 순으로 정렬
            sorted_stocks = sorted(portfolio_data, key=lambda x: x['name'])
            
            # 중복 방지
            added_stock_ids = set()
            unique_stocks = []
            for stock_data in sorted_stocks:
                stock_id = stock_data['id']
                if stock_id not in added_stock_ids:
                    added_stock_ids.add(stock_id)
                    unique_stocks.append(stock_data)
            
            # 그리드 레이아웃
            num_cols = min(9, len(unique_stocks))
            if num_cols > 0:
                # 첫 번째 줄
                badge_cols = st.columns(num_cols)
                for idx, stock_data in enumerate(unique_stocks[:num_cols]):
                    name = stock_data['name']
                    progress = stock_data['progress']
                    stock_id = stock_data['id']
                    progress_pct = min(100, max(0, progress))
                    
                    with badge_cols[idx]:
                        if create_overlay_badge(name, progress_pct, f"badge_{stock_id}"):
                            # 뱃지 클릭 시 dialog 직접 호출
                            show_stock_detail_modal(stock_id)
                
                # 나머지 줄들
                remaining = unique_stocks[num_cols:]
                row_num = 0
                while remaining:
                    row_stocks = remaining[:num_cols]
                    remaining = remaining[num_cols:]
                    if row_stocks:
                        row_cols = st.columns(num_cols)
                        for col_idx, stock_data in enumerate(row_stocks):
                            name = stock_data['name']
                            progress = stock_data['progress']
                            stock_id = stock_data['id']
                            progress_pct = min(100, max(0, progress))
                            
                            with row_cols[col_idx]:
                                if create_overlay_badge(name, progress_pct, f"badge_{stock_id}_r{row_num}"):
                                    # 뱃지 클릭 시 dialog 직접 호출
                                    show_stock_detail_modal(stock_id)
                        row_num += 1
            
        
        # 전체 현황판 (드롭다운 기능 포함)
        if portfolio_data:
            # 정렬 상태 관리
            if 'portfolio_sort_col' not in st.session_state:
                st.session_state['portfolio_sort_col'] = 'totalInvested'
            if 'portfolio_sort_asc' not in st.session_state:
                st.session_state['portfolio_sort_asc'] = False
            if 'portfolio_table_expanded' not in st.session_state:
                st.session_state['portfolio_table_expanded'] = True
            
            display_df = pd.DataFrame(portfolio_data)
            display_df['percentage'] = (display_df['totalInvested'] / total_invested * 100) if total_invested > 0 else 0
            
            # 정렬 적용
            display_df = display_df.sort_values(
                st.session_state['portfolio_sort_col'], 
                ascending=st.session_state['portfolio_sort_asc']
            )
            
            # 드롭다운으로 테이블 접기/펼치기
            with st.expander("### 전체 현황판", expanded=st.session_state['portfolio_table_expanded']):
                # expander가 열려있을 때만 테이블 표시
                if st.session_state['portfolio_table_expanded']:
            
                    # 커스텀 테이블 스타일
                    st.markdown("""
                    <style>
                    .portfolio-table {
                        background: rgba(30, 41, 59, 0.5);
                        border-radius: 10px;
                        padding: 1rem;
                        margin-top: 1rem;
                    }
                    .portfolio-table-header {
                        display: grid;
                        grid-template-columns: 0.5fr 1fr 2fr 2fr 1fr;
                        gap: 1rem;
                        padding: 1rem;
                        background: rgba(99, 102, 241, 0.2);
                        border-radius: 8px;
                        margin-bottom: 0.5rem;
                        font-weight: 600;
                        color: #ffffff;
                    }
                    .portfolio-table-header-cell {
                        cursor: pointer;
                        user-select: none;
                        transition: background 0.2s;
                        padding: 0.3rem;
                        border-radius: 4px;
                    }
                    .portfolio-table-header-cell:hover {
                        background: rgba(99, 102, 241, 0.3);
                    }
                    .portfolio-table-row {
                        display: grid;
                        grid-template-columns: 0.5fr 1fr 2fr 2fr 1fr;
                        gap: 1rem;
                        padding: 0.8rem 1rem;
                        background: rgba(59, 130, 246, 0.15);
                        border-radius: 6px;
                        margin-bottom: 0.3rem;
                        align-items: center;
                        transition: background 0.2s;
                    }
                    .portfolio-table-row:hover {
                        background: rgba(59, 130, 246, 0.25);
                    }
                    .stock-name-link {
                        color: #60a5fa !important;
                        cursor: pointer;
                        text-decoration: underline;
                        font-weight: 500;
                    }
                    .stock-name-link:hover {
                        color: #3b82f6 !important;
                    }
                    .progress-bar-container {
                        width: 100%;
                        height: 24px;
                        background: rgba(55, 65, 81, 0.5);
                        border-radius: 12px;
                        overflow: hidden;
                        position: relative;
                    }
                    .progress-bar-fill {
                        height: 100%;
                        background: linear-gradient(90deg, #3b82f6, #60a5fa);
                        border-radius: 12px;
                        transition: width 0.3s;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: #ffffff;
                        font-weight: 600;
                        font-size: 0.85rem;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # 테이블 헤더 (클릭 가능한 정렬 버튼)
                    # 종목명 가로 길이를 행과 동일하게 맞춤
                    header_cols = st.columns([0.5, 1, 2, 2, 1])
                    with header_cols[0]:
                        st.markdown("<div style='text-align: center; font-weight: 600; color: #ffffff;'>#</div>", unsafe_allow_html=True)
                    
                    # 정렬 가능한 헤더 생성
                    sortable_headers = [
                        ("종목명", "name", header_cols[1]),
                        ("현재 매입금액 (% 비중)", "totalInvested", header_cols[2]),
                        ("매수 진행률", "progress", header_cols[3]),
                        ("비중", "percentage", header_cols[4])
                    ]
                    
                    for header_text, col_name, col in sortable_headers:
                        with col:
                            is_current_sort = st.session_state['portfolio_sort_col'] == col_name
                            sort_indicator = ""
                            if is_current_sort:
                                sort_indicator = " ↑" if st.session_state['portfolio_sort_asc'] else " ↓"
                            
                            if st.button(f"{header_text}{sort_indicator}", key=f"sort_{col_name}", use_container_width=True):
                                if st.session_state['portfolio_sort_col'] == col_name:
                                    # 같은 컬럼 클릭 시 오름차순/내림차순 토글
                                    st.session_state['portfolio_sort_asc'] = not st.session_state['portfolio_sort_asc']
                                else:
                                    # 다른 컬럼 클릭 시 내림차순으로 설정
                                    st.session_state['portfolio_sort_col'] = col_name
                                    st.session_state['portfolio_sort_asc'] = False
                                st.rerun()
                            
                            # 헤더 버튼 스타일
                            st.markdown(f"""
                            <style>
                            button[key="sort_{col_name}"] {{
                                background: rgba(99, 102, 241, 0.2) !important;
                                color: #ffffff !important;
                                font-weight: 600 !important;
                                border: none !important;
                                cursor: pointer !important;
                            }}
                            button[key="sort_{col_name}"]:hover {{
                                background: rgba(99, 102, 241, 0.3) !important;
                            }}
                            </style>
                            """, unsafe_allow_html=True)
                    
                    # 테이블 행
                    for row_idx, (_, row) in enumerate(display_df.iterrows()):
                        name = row['name']
                        invested = row['totalInvested']
                        progress = row['progress']
                        percentage = row['percentage']
                        stock_id = row.get('id', '')
                        
                        # 진행률에 따른 색상
                        if progress >= 100:
                            progress_color = "#10b981"
                        elif progress >= 50:
                            progress_color = "#3b82f6"
                        else:
                            progress_color = "#6366f1"
                        
                        # 종목명 클릭 시 해당 종목으로 이동
                        # 종목명 가로 길이를 더 줄임 (이수스페셜티케미칼이 한 줄로 표시되도록)
                        row_cols = st.columns([0.5, 1, 2, 2, 1])
                        with row_cols[0]:
                            st.markdown(f"<div style='text-align: center; color: #9ca3af;'>{row_idx + 1}</div>", unsafe_allow_html=True)
                        with row_cols[1]:
                            if st.button(name, key=f"stock_link_{stock_id}_{row_idx}", use_container_width=True):
                                # 종목명 클릭 시 dialog 직접 호출
                                show_stock_detail_modal(stock_id)
                            # 종목명 버튼에 고유 클래스 추가를 위한 JavaScript
                            st.markdown(f"""
                            <script>
                            (function() {{
                                function styleStockButton() {{
                                    // 버튼 텍스트로 종목명 버튼 찾기
                                    const buttons = document.querySelectorAll('.stButton > button');
                                    buttons.forEach(button => {{
                                        const buttonText = button.textContent.trim() || 
                                                         button.querySelector('p')?.textContent.trim() || 
                                                         button.querySelector('span')?.textContent.trim() || '';
                                        if (buttonText === '{name}') {{
                                            // 초록색 스타일 적용
                                            button.style.cssText = `
                                                background: rgba(16, 185, 129, 0.2) !important;
                                                color: #10b981 !important;
                                                text-decoration: none !important;
                                                font-weight: 500 !important;
                                                border: 1px solid rgba(16, 185, 129, 0.3) !important;
                                                box-shadow: 0 2px 4px rgba(16, 185, 129, 0.1) !important;
                                                border-radius: 6px !important;
                                                padding: 0.4rem 0.6rem !important;
                                                white-space: nowrap !important;
                                                overflow: hidden !important;
                                                text-overflow: ellipsis !important;
                                            `;
                                            
                                            // 호버 이벤트
                                            button.addEventListener('mouseenter', function() {{
                                                this.style.background = 'rgba(16, 185, 129, 0.3)';
                                                this.style.color = '#059669';
                                                this.style.borderColor = 'rgba(16, 185, 129, 0.5)';
                                                this.style.boxShadow = '0 4px 6px rgba(16, 185, 129, 0.2)';
                                            }});
                                            button.addEventListener('mouseleave', function() {{
                                                this.style.background = 'rgba(16, 185, 129, 0.2)';
                                                this.style.color = '#10b981';
                                                this.style.borderColor = 'rgba(16, 185, 129, 0.3)';
                                                this.style.boxShadow = '0 2px 4px rgba(16, 185, 129, 0.1)';
                                            }});
                                            
                                            // 내부 텍스트 색상
                                            const textElements = button.querySelectorAll('p, span');
                                            textElements.forEach(el => {{
                                                el.style.color = '#10b981';
                                            }});
                                        }}
                                    }});
                                }}
                                
                                if (document.readyState === 'loading') {{
                                    document.addEventListener('DOMContentLoaded', styleStockButton);
                                }} else {{
                                    styleStockButton();
                                }}
                                
                                // MutationObserver로 동적 추가 감지
                                const observer = new MutationObserver(styleStockButton);
                                observer.observe(document.body, {{ childList: true, subtree: true }});
                                
                                // 짧은 지연 후 재시도
                                setTimeout(styleStockButton, 100);
                                setTimeout(styleStockButton, 500);
                            }})();
                            </script>
                            """, unsafe_allow_html=True)
                        with row_cols[2]:
                            st.markdown(f"<div style='color: #ffffff;'>₩{invested:,.0f} ({percentage:.1f}%)</div>", unsafe_allow_html=True)
                        with row_cols[3]:
                            st.markdown(f"""
                            <div class="progress-bar-container">
                                <div class="progress-bar-fill" style="width: {min(100, max(0, progress))}%; background: linear-gradient(90deg, {progress_color}, {progress_color}dd);">
                                    {progress:.2f}%
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        with row_cols[4]:
                            st.markdown(f"<div style='text-align: center; color: #9ca3af;'>{percentage:.1f}%</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # ==========================================
    # 2. 종목별 카드 표시
    # ==========================================
    # 기존 Expander 루프는 제거됨 - 클릭 시에만 dialog 호출
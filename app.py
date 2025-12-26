import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import os
import time
import json
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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

    /* === 5. 버튼 스타일 === */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: #FFFFFF !important; /* 버튼 글씨는 흰색 */
        border: none !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
    }
    /* 버튼 내부 텍스트 흰색 강제 */
    .stButton > button p {
        color: #FFFFFF !important;
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
    /* 사이드바 버튼 */
    section[data-testid="stSidebar"] button {
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
    
    /* 버튼 스타일 개선 */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.4rem 1rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4) !important;
    }
    
    /* 수정 버튼 스타일 (secondary 타입을 파란색 계열로) */
    .stButton > button[kind="secondary"],
    div[data-testid="stDialog"] .stButton > button[kind="secondary"],
    div[role="dialog"] .stButton > button[kind="secondary"],
    button[kind="secondary"] {
        background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.4rem 1rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button[kind="secondary"] p,
    div[data-testid="stDialog"] .stButton > button[kind="secondary"] p,
    div[role="dialog"] .stButton > button[kind="secondary"] p,
    button[kind="secondary"] p {
        color: #FFFFFF !important;
    }
    
    .stButton > button[kind="secondary"]:hover,
    div[data-testid="stDialog"] .stButton > button[kind="secondary"]:hover,
    div[role="dialog"] .stButton > button[kind="secondary"]:hover,
    button[kind="secondary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
        color: #FFFFFF !important;
    }
    
    .stButton > button[kind="secondary"]:hover p,
    div[data-testid="stDialog"] .stButton > button[kind="secondary"]:hover p,
    div[role="dialog"] .stButton > button[kind="secondary"]:hover p,
    button[kind="secondary"]:hover p {
        color: #FFFFFF !important;
    }
    
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
    
    /* Dialog 내부 모든 텍스트 - 흰색 */
    div[data-testid="stDialog"] *,
    div[role="dialog"] *,
    section[data-testid="stDialog"] *,
    section[role="dialog"] * {
        color: #FFFFFF !important;
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
    
    /* Dialog 내부 버튼 - primary 타입만 보라색, secondary는 파란색 */
    div[data-testid="stDialog"] .stButton > button[kind="primary"],
    div[role="dialog"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: #FFFFFF !important;
    }
    
    /* Dialog 내부 secondary 버튼 (수정 버튼) - 파란색 */
    div[data-testid="stDialog"] .stButton > button[kind="secondary"],
    div[role="dialog"] .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    
    div[data-testid="stDialog"] .stButton > button[kind="secondary"] p,
    div[role="dialog"] .stButton > button[kind="secondary"] p {
        color: #FFFFFF !important;
    }
    
    div[data-testid="stDialog"] .stButton > button[kind="secondary"]:hover,
    div[role="dialog"] .stButton > button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
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
        expected_columns = ["Symbol", "Name", "InterestDate", "Note", "MarketCap", "Installments", "Category", "BuyTransactions", "SellTransactions"]
        
        if not headers or headers != expected_columns:
            # 헤더 업데이트
            worksheet.clear()
            worksheet.append_row(expected_columns)
            st.info("✅ Google Sheets 헤더가 통합 구조로 업데이트되었습니다.")
        
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
            columns = ["Symbol", "Name", "InterestDate", "Note", "MarketCap", "Installments", "Category", "BuyTransactions", "SellTransactions"]
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
        columns = ["Symbol", "Name", "InterestDate", "Note", "MarketCap", "Installments", "Category", "BuyTransactions", "SellTransactions"]
        return pd.DataFrame(columns=columns)

# Google Sheets에 데이터 저장 (통합 시트)
def save_stocks(df):
    """DataFrame을 Google Sheets에 저장합니다 (통합 시트)."""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet("Stocks")
        
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
        
        # 헤더 포함 전체 데이터 준비
        values = [df.columns.tolist()] + df.values.tolist()
        
        # 기존 데이터 지우고 새 데이터 쓰기
        worksheet.clear()
        worksheet.update(values, value_input_option='USER_ENTERED')
        
        # 캐시 무효화 (다음 로드 시 최신 데이터 가져오기)
        load_stocks.clear()
        load_split_purchase_data.clear()  # 분할 매수 플래너 캐시도 초기화
        
    except Exception as e:
        st.error(f"❌ 데이터 저장 실패: {str(e)}")
        raise

# 주가 데이터 가져오기 (캐싱 + 재시도 로직)
@st.cache_data(ttl=7200)  # 2시간 캐싱 (rate limiting 방지)
def get_stock_data(symbol):
    max_retries = 3
    retry_delay = 2  # 초기 지연 시간 (초)
    
    for attempt in range(max_retries):
        try:
            # 요청 간 지연 (rate limiting 방지)
            if attempt > 0:
                time.sleep(retry_delay * (attempt + 1))  # 지수 백오프
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="max")
            
            # 빈 데이터 체크
            if df.empty:
                if attempt < max_retries - 1:
                    continue
                st.warning(f"{symbol} 종목의 데이터가 비어있습니다. 티커를 확인해주세요.")
                return None
            
            # 타임존 정보 제거 (yfinance 데이터의 인덱스에 타임존이 포함되어 있어서 제거)
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            # 인덱스를 날짜만 남기고 시간 정보 제거 (정규화)
            df.index = pd.to_datetime(df.index).normalize()
            return df
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Rate limiting 오류 감지
            if "too many requests" in error_msg or "rate limit" in error_msg or "429" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # 지수 백오프
                    st.warning(f"요청이 너무 많습니다. {wait_time}초 후 재시도합니다... ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    st.error(f"❌ API 요청 한도에 도달했습니다. 잠시 후 다시 시도해주세요.")
                    st.info("💡 팁: 잠시 기다린 후 페이지를 새로고침하거나, 다른 종목을 먼저 확인해보세요.")
                    return None
            
            # 기타 오류
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                st.error(f"❌ {symbol} 종목의 데이터를 가져올 수 없습니다: {str(e)}")
                st.info("💡 티커 형식을 확인해주세요. 예: AAPL, 005930.KS, TSLA")
                return None
    
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
        
        # Symbol 기준으로 기존 데이터 업데이트 또는 추가
        for idx, row in df.iterrows():
            symbol = row.get('Symbol', '')
            if symbol:
                # 기존 데이터에서 해당 Symbol 찾기
                mask = all_df['Symbol'] == symbol
                if mask.any():
                    # 업데이트
                    all_df.loc[mask, row.index] = row.values
                else:
                    # 새 행 추가
                    all_df = pd.concat([all_df, pd.DataFrame([row])], ignore_index=True)
        
        # 빈 값 처리
        all_df = all_df.fillna("")
        
        # 전체 데이터 저장
        values = [all_df.columns.tolist()] + all_df.values.tolist()
        ws.clear()
        ws.update(values, value_input_option='USER_ENTERED')
        
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
        # 상단 컨트롤 바 (5단 구성)
        col1, col2, col3, col4, col5 = st.columns([1, 1.5, 0.8, 0.8, 1])
        
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
                        filtered_options.append(f"{row['Name']} ({row['Symbol']})")
                if filtered_options:
                    stock_options = filtered_options
            elif category == "관심종목":
                filtered_options = []
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
                        filtered_options.append(f"{row['Name']} ({row['Symbol']})")
                if filtered_options:
                    stock_options = filtered_options
            
            # 가나다순 정렬
            stock_options = sorted(stock_options)
            
            selected_stock = st.selectbox("종목 선택", stock_options, key="stock_select")
        
        with col3:
            # 시작일
            start_date = st.date_input(
                "시작일",
                value=None,
                key="start_date"
            )
        
        with col4:
            # 종료일
            end_date = st.date_input(
                "종료일",
                value=None,
                key="end_date"
            )
        
        with col5:
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
            selected_name_symbol = selected_stock
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
        
        # 투자 현황 계산
        total_buy_cost = 0
        total_buy_qty = 0
        for tx in buy_txs:
            if isinstance(tx, dict):
                total_buy_cost += tx.get('price', 0) * tx.get('quantity', 0)
                total_buy_qty += tx.get('quantity', 0)
        
        total_sell_qty = sum(tx.get('quantity', 0) for tx in sell_txs if isinstance(tx, dict))
        avg_price = total_buy_cost / total_buy_qty if total_buy_qty > 0 else 0
        current_qty = total_buy_qty - total_sell_qty
        current_invested = current_qty * avg_price
        progress = (current_invested / max_investment * 100) if max_investment > 0 else 0
        
        # 실현 손익 계산
        total_realized_profit = 0
        for tx in sell_txs:
            if isinstance(tx, dict) and avg_price > 0:
                profit = (tx.get('price', 0) - avg_price) * tx.get('quantity', 0)
                total_realized_profit += profit
        
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
                                button_type = "secondary"  # 수정 버튼은 secondary (파란색 계열)
                            else:
                                button_label = "기록"
                                button_type = "primary"  # 기록 버튼은 primary (빨간색)
                            
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
                        profit = (tx.get('price', 0) - avg_price) * tx.get('quantity', 0) if avg_price > 0 else 0
                        yield_pct = ((tx.get('price', 0) - avg_price) / avg_price * 100) if avg_price > 0 else 0
                        
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
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.subheader("📊 포트폴리오 요약")
    with col_header2:
        # 우측 상단 버튼 영역
        st.markdown("<br>", unsafe_allow_html=True)  # 여백
        with st.expander("➕ 새 종목 추가", expanded=False):
            with st.form("add_split_stock_form"):
                symbol = st.text_input("티커 (예: AAPL, 005930.KS)", placeholder="예: 005930.KS", key="split_symbol_input")
                name = st.text_input("종목명", placeholder="예: 삼성전자", key="split_name_input")
                interest_date = st.date_input("관심일", value=None, key="split_interest_date_input")
                market_cap = st.number_input("시가총액 (억원)", min_value=0, step=1000, placeholder="예: 5000000", key="split_market_cap_input")
                installments = st.number_input("분할 횟수", min_value=1, value=3, key="split_installments_input")
                category = st.selectbox("투자 전략", options=["Long", "Short"], key="split_category_input")
                
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
                interest_options = [f"{s['Name']} ({s['Symbol']})" for s in interest_stocks]
                selected_interest = st.selectbox("관심종목 선택", interest_options, key="select_interest_stock")
                
                with st.form("import_interest_stock_form"):
                    # 선택된 종목 정보 표시
                    selected_idx = interest_options.index(selected_interest) if selected_interest in interest_options else -1
                    if selected_idx >= 0:
                        selected_stock = interest_stocks[selected_idx]
                        st.info(f"선택된 종목: {selected_stock['Name']} ({selected_stock['Symbol']})")
                    
                    market_cap = st.number_input("시가총액 (억원)", min_value=0, step=1000, placeholder="예: 5000000", key="import_market_cap")
                    installments = st.number_input("분할 횟수", min_value=1, value=3, key="import_installments")
                    category = st.selectbox("투자 전략", options=["Long", "Short"], key="import_category")
                    
                    if st.form_submit_button("분할 매수 플래너에 추가"):
                        if selected_idx >= 0 and market_cap > 0:
                            selected_stock = interest_stocks[selected_idx]
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
        
        # 요약 메트릭 (하단에 표시)
        col_summary1, col_summary2 = st.columns(2)
        with col_summary1:
            st.markdown(f"""
            <div style="
                background: rgba(99, 102, 241, 0.1);
                border-radius: 10px;
                padding: 1.5rem;
                margin-bottom: 1rem;
            ">
                <div style="color: #9ca3af; font-size: 0.9rem; margin-bottom: 0.5rem;">총 예산</div>
                <div style="color: #ffffff; font-size: 1.8rem; font-weight: 700;">₩{total_budget:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_summary2:
            st.markdown(f"""
            <div style="
                background: rgba(99, 102, 241, 0.1);
                border-radius: 10px;
                padding: 1.5rem;
                margin-bottom: 1rem;
            ">
                <div style="color: #9ca3af; font-size: 0.9rem; margin-bottom: 0.5rem;">진행률</div>
                <div style="color: #60a5fa; font-size: 1.8rem; font-weight: 700;">{overall_progress:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 도넛 차트 (개선된 버전)
        if total_invested > 0:
            colors = px.colors.qualitative.Plotly
            chart_df = pd.DataFrame(portfolio_data)
            chart_df = chart_df[chart_df['totalInvested'] > 0].sort_values('totalInvested', ascending=False)
            
            if not chart_df.empty:
                fig_donut = px.pie(
                    chart_df,
                    values='totalInvested',
                    names='name',
                    hole=0.6,
                    color_discrete_sequence=colors
                )
                # 중앙에 총 매입금액 표시
                fig_donut.update_traces(
                    textposition='outside',
                    textinfo='label+percent',
                    hovertemplate='<b>%{label}</b><br>매입금액: ₩%{value:,.0f}<br>비중: %{percent}<extra></extra>'
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
                        font=dict(color='#ffffff', size=12, family='Pretendard')
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#ffffff', family='Pretendard'),
                    height=500,
                    margin=dict(l=0, r=150, t=80, b=0)
                )
                st.plotly_chart(fig_donut, use_container_width=True)
        
        # 매수종목 뱃지 (그라데이션으로 진행률 표시)
        if portfolio_data:
            st.markdown("### 종목별 현황")
            
            # 오버레이 뱃지 생성 함수
            def create_overlay_badge(name, progress, key):
                """CSS 오버레이 기법으로 뱃지 생성 (렌더링 통합 + 강력한 선택자)"""
                progress_pct = min(100, max(0, progress))
                dark_green = '#10b981'
                light_green = '#86efac'
                gradient = f'linear-gradient(to right, {dark_green} 0%, {dark_green} {progress_pct}%, {light_green} {progress_pct}%, {light_green} 100%)'
                
                # HTML과 CSS를 하나의 st.markdown으로 통합 렌더링
                st.markdown(f"""
                <style>
                /* 강력한 선택자: 뱃지가 들어있는 div의 바로 다음 형제 div 안의 버튼 타겟팅 */
                div:has(> .badge-overlay-visual) + div button,
                div:has(.badge-overlay-visual) + div[data-testid="stButton"] button,
                div[data-testid="stMarkdownContainer"]:has(.badge-overlay-visual) + div[data-testid="stButton"] button,
                div[data-testid="stMarkdownContainer"]:has(.badge-overlay-visual) ~ div[data-testid="stButton"] button {{
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
                }}
                /* 버튼 컨테이너 위치 조정 */
                div:has(> .badge-overlay-visual) + div[data-testid="stButton"],
                div:has(.badge-overlay-visual) + div[data-testid="stButton"],
                div[data-testid="stMarkdownContainer"]:has(.badge-overlay-visual) + div[data-testid="stButton"] {{
                    margin-top: -48px !important;
                    position: relative !important;
                    z-index: 10 !important;
                }}
                </style>
                <div class="badge-overlay-visual" style="
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
                ">{name}</div>
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
                        grid-template-columns: 0.5fr 2fr 2fr 2fr 1fr;
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
                        grid-template-columns: 0.5fr 1.33fr 2fr 2fr 1fr;
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
                    # 종목명 가로 길이를 2/3로 줄임: 2 * 2/3 = 1.33
                    header_cols = st.columns([0.5, 1.33, 2, 2, 1])
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
                        # 종목명 가로 길이를 2/3로 줄임: 2 * 2/3 = 1.33
                        row_cols = st.columns([0.5, 1.33, 2, 2, 1])
                        with row_cols[0]:
                            st.markdown(f"<div style='text-align: center; color: #9ca3af;'>{row_idx + 1}</div>", unsafe_allow_html=True)
                        with row_cols[1]:
                            if st.button(name, key=f"stock_link_{stock_id}_{row_idx}", use_container_width=True):
                                # 종목명 클릭 시 dialog 직접 호출
                                show_stock_detail_modal(stock_id)
                            st.markdown(f"""
                            <style>
                            button[key="stock_link_{stock_id}_{row_idx}"] {{
                                background: transparent !important;
                                color: #60a5fa !important;
                                text-decoration: underline !important;
                                font-weight: 500 !important;
                                border: none !important;
                                box-shadow: none !important;
                            }}
                            button[key="stock_link_{stock_id}_{row_idx}"]:hover {{
                                color: #3b82f6 !important;
                            }}
                            </style>
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
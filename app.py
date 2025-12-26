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
        
        # 워크시트 찾기 또는 생성
        try:
            worksheet = spreadsheet.worksheet("Stocks1")
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title="Stocks1", rows=1000, cols=30)
        
        # 헤더 확인 및 추가
        headers = worksheet.row_values(1)
        expected_columns = ["Symbol", "Name", "InterestDate", "Note"]
        for i in range(1, 11):
            expected_columns.append(f"BuyDate{i}")
            expected_columns.append(f"SellDate{i}")
        
        if not headers or headers != expected_columns:
            # 헤더 업데이트
            worksheet.clear()
            worksheet.append_row(expected_columns)
            st.info("✅ Google Sheets 헤더가 업데이트되었습니다.")
        
        return spreadsheet, worksheet
    except Exception as e:
        st.error(f"❌ Google Sheets 초기화 실패: {str(e)}")
        st.stop()

# Google Sheets에서 데이터 읽기
@st.cache_data(ttl=60)  # 1분 캐싱 (데이터 변경 시 빠른 반영)
def load_stocks():
    """Google Sheets에서 종목 데이터를 로드합니다."""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet("Stocks1")
        
        # 모든 데이터 가져오기
        records = worksheet.get_all_records()
        
        if not records:
            # 빈 DataFrame 반환 (헤더만 있는 경우)
            columns = ["Symbol", "Name", "InterestDate", "Note"]
            for i in range(1, 11):
                columns.append(f"BuyDate{i}")
                columns.append(f"SellDate{i}")
            return pd.DataFrame(columns=columns)
        
        # DataFrame으로 변환
        df = pd.DataFrame(records)
        
        # 빈 값 처리 (Google Sheets는 빈 셀을 빈 문자열로 반환)
        df = df.replace("", pd.NA)
        
        return df
    except Exception as e:
        st.error(f"❌ 데이터 로드 실패: {str(e)}")
        # 빈 DataFrame 반환
        columns = ["Symbol", "Name", "InterestDate", "Note"]
        for i in range(1, 11):
            columns.append(f"BuyDate{i}")
            columns.append(f"SellDate{i}")
        return pd.DataFrame(columns=columns)

# Google Sheets에 데이터 저장
def save_stocks(df):
    """DataFrame을 Google Sheets에 저장합니다."""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet("Stocks1")
        
        # 빈 값 처리 (pd.NA를 빈 문자열로 변환)
        df = df.fillna("")
        
        # 헤더 포함 전체 데이터 준비
        values = [df.columns.tolist()] + df.values.tolist()
        
        # 기존 데이터 지우고 새 데이터 쓰기
        worksheet.clear()
        worksheet.update(values, value_input_option='USER_ENTERED')
        
        # 캐시 무효화 (다음 로드 시 최신 데이터 가져오기)
        load_stocks.clear()
        
    except Exception as e:
        st.error(f"❌ 데이터 저장 실패: {str(e)}")
        raise

# 주가 데이터 가져오기 (캐싱)
@st.cache_data(ttl=3600)  # 1시간 캐싱
def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="max")
        # 타임존 정보 제거 (yfinance 데이터의 인덱스에 타임존이 포함되어 있어서 제거)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        # 인덱스를 날짜만 남기고 시간 정보 제거 (정규화)
        df.index = pd.to_datetime(df.index).normalize()
        return df
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {str(e)}")
        return None

# ==========================================
# 분할 매수 플래너 관련 함수들
# ==========================================

# 분할 매수 플래너 데이터 로드
@st.cache_data(ttl=60)
def load_split_purchase_data():
    """SplitPurchasePlanner 시트에서 데이터를 로드합니다."""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        
        try:
            ws = spreadsheet.worksheet("SplitPurchasePlanner")
            records = ws.get_all_records()
            
            if not records:
                return pd.DataFrame(columns=["ID", "Name", "MarketCap", "Installments", "BuyTransactions", "SellTransactions"])
            
            df = pd.DataFrame(records)
            return df
        except gspread.WorksheetNotFound:
            # 워크시트가 없으면 생성
            ws = spreadsheet.add_worksheet(title="SplitPurchasePlanner", rows=1000, cols=10)
            headers = ["ID", "Name", "MarketCap", "Installments", "BuyTransactions", "SellTransactions"]
            ws.append_row(headers)
            return pd.DataFrame(columns=headers)
    except Exception as e:
        st.error(f"❌ 분할 매수 데이터 로드 실패: {str(e)}")
        return pd.DataFrame(columns=["ID", "Name", "MarketCap", "Installments", "BuyTransactions", "SellTransactions"])

# 분할 매수 플래너 데이터 저장
def save_split_purchase_data(df):
    """SplitPurchasePlanner 시트에 데이터를 저장합니다."""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        ws = spreadsheet.worksheet("SplitPurchasePlanner")
        
        # JSON 컬럼을 문자열로 변환
        df = df.copy()
        if 'BuyTransactions' in df.columns:
            df['BuyTransactions'] = df['BuyTransactions'].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else (x if x else '[]'))
        if 'SellTransactions' in df.columns:
            df['SellTransactions'] = df['SellTransactions'].apply(lambda x: json.dumps(x) if isinstance(x, list) else (x if x else '[]'))
        
        df = df.fillna("")
        values = [df.columns.tolist()] + df.values.tolist()
        
        ws.clear()
        ws.update(values, value_input_option='USER_ENTERED')
        
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
    buy_date = st.session_state.get("buy_date_input", None)
    sell_date = st.session_state.get("sell_date_input", None)
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
                "Note": note if note else ""
            }
            # BuyDate1~10, SellDate1~10 초기화
            for i in range(1, 11):
                new_row[f"BuyDate{i}"] = ""
                new_row[f"SellDate{i}"] = ""
            # 첫 번째 매수일/매도일 설정
            if buy_date:
                new_row["BuyDate1"] = buy_date.strftime("%Y-%m-%d")
            if sell_date:
                new_row["SellDate1"] = sell_date.strftime("%Y-%m-%d")
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_stocks(df)
            
            # 성공 시 입력값 초기화
            st.session_state["symbol_input"] = ""
            st.session_state["name_input"] = ""
            st.session_state["interest_date_input"] = None
            st.session_state["buy_date_input"] = None
            st.session_state["sell_date_input"] = None
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
        buy_date = st.date_input("매수일 (선택사항)", value=None, key="buy_date_input")
        sell_date = st.date_input("매도일 (선택사항)", value=None, key="sell_date_input")
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
            
            # 카테고리 필터링
            if category == "매수종목":
                filtered_options = []
                for idx, row in df.iterrows():
                    # BuyDate1~10 중 하나라도 있으면 매수종목
                    has_buy_date = False
                    for i in range(1, 11):
                        if pd.notna(row.get(f'BuyDate{i}', '')) and str(row.get(f'BuyDate{i}', '')).strip() != "":
                            has_buy_date = True
                            break
                    if has_buy_date:
                        filtered_options.append(f"{row['Name']} ({row['Symbol']})")
                if filtered_options:
                    stock_options = filtered_options
            elif category == "관심종목":
                filtered_options = []
                for idx, row in df.iterrows():
                    # BuyDate1~10이 모두 비어있고 InterestDate가 있으면 관심종목
                    has_buy_date = False
                    for i in range(1, 11):
                        if pd.notna(row.get(f'BuyDate{i}', '')) and str(row.get(f'BuyDate{i}', '')).strip() != "":
                            has_buy_date = True
                            break
                    if not has_buy_date and pd.notna(row.get('InterestDate', '')) and str(row.get('InterestDate', '')).strip() != "":
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
                
                # BuyDate1~10, SellDate1~10 읽기
                buy_dates = []
                sell_dates = []
                for i in range(1, 11):
                    buy_date_val = selected_row.get(f'BuyDate{i}', '')
                    if pd.notna(buy_date_val) and str(buy_date_val).strip() != "":
                        buy_dates.append(str(buy_date_val).strip())
                    else:
                        buy_dates.append("")
                    sell_date_val = selected_row.get(f'SellDate{i}', '')
                    if pd.notna(sell_date_val) and str(sell_date_val).strip() != "":
                        sell_dates.append(str(sell_date_val).strip())
                    else:
                        sell_dates.append("")
                
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
                        
                        # 매수일 입력 (동적 추가)
                        st.write("**매수일**")
                        buy_date_inputs = []
                        buy_date_count = len([d for d in buy_dates if d != ""]) or 1
                        if buy_date_count == 0:
                            buy_date_count = 1
                        
                        # 세션 상태로 매수일 개수 관리
                        if f'buy_date_count_{symbol}' not in st.session_state:
                            st.session_state[f'buy_date_count_{symbol}'] = max(buy_date_count, 1)
                        
                        for i in range(st.session_state[f'buy_date_count_{symbol}']):
                            col_date, col_delete = st.columns([4, 1])
                            with col_date:
                                buy_date_inputs.append(st.date_input(
                                    f"매수일 {i+1}",
                                    value=parse_date(buy_dates[i]) if i < len(buy_dates) else None,
                                    key=f"edit_buy_date_{i}_{symbol}",
                                    label_visibility="collapsed"
                                ))
                            with col_delete:
                                if st.button("🗑️", key=f"delete_buy_date_{i}_{symbol}", help="삭제", type="secondary"):
                                    # 즉시 CSV에서 해당 날짜 삭제
                                    df_stocks = load_stocks()
                                    mask = df_stocks['Symbol'] == symbol
                                    if mask.any():
                                        # i는 0부터 시작하므로 BuyDate{i+1}에 해당
                                        date_idx = i + 1
                                        # 해당 인덱스의 BuyDate를 None으로 명시적 할당
                                        df_stocks.loc[mask, f'BuyDate{date_idx}'] = None
                                        # 뒤의 날짜들을 앞으로 이동
                                        for j in range(date_idx, 10):
                                            next_val = df_stocks.loc[mask, f'BuyDate{j+1}'].values[0] if mask.any() else None
                                            if pd.notna(next_val) and str(next_val).strip() != "":
                                                df_stocks.loc[mask, f'BuyDate{j}'] = str(next_val).strip()
                                            else:
                                                df_stocks.loc[mask, f'BuyDate{j}'] = ""
                                        df_stocks.loc[mask, 'BuyDate10'] = ""
                                        # 즉시 저장
                                        save_stocks(df_stocks)
                                        st.success("삭제되었습니다!")
                                        # 0.5초 대기
                                        time.sleep(0.5)
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
                        
                        # 매도일 입력 (동적 추가)
                        st.write("**매도일**")
                        sell_date_inputs = []
                        sell_date_count = len([d for d in sell_dates if d != ""]) or 1
                        if sell_date_count == 0:
                            sell_date_count = 1
                        
                        # 세션 상태로 매도일 개수 관리
                        if f'sell_date_count_{symbol}' not in st.session_state:
                            st.session_state[f'sell_date_count_{symbol}'] = max(sell_date_count, 1)
                        
                        for i in range(st.session_state[f'sell_date_count_{symbol}']):
                            col_date, col_delete = st.columns([4, 1])
                            with col_date:
                                sell_date_inputs.append(st.date_input(
                                    f"매도일 {i+1}",
                                    value=parse_date(sell_dates[i]) if i < len(sell_dates) else None,
                                    key=f"edit_sell_date_{i}_{symbol}",
                                    label_visibility="collapsed"
                                ))
                            with col_delete:
                                if st.button("🗑️", key=f"delete_sell_date_{i}_{symbol}", help="삭제", type="secondary"):
                                    # 즉시 CSV에서 해당 날짜 삭제
                                    df_stocks = load_stocks()
                                    mask = df_stocks['Symbol'] == symbol
                                    if mask.any():
                                        # i는 0부터 시작하므로 SellDate{i+1}에 해당
                                        date_idx = i + 1
                                        # 해당 인덱스의 SellDate를 None으로 명시적 할당
                                        df_stocks.loc[mask, f'SellDate{date_idx}'] = None
                                        # 뒤의 날짜들을 앞으로 이동
                                        for j in range(date_idx, 10):
                                            next_val = df_stocks.loc[mask, f'SellDate{j+1}'].values[0] if mask.any() else None
                                            if pd.notna(next_val) and str(next_val).strip() != "":
                                                df_stocks.loc[mask, f'SellDate{j}'] = str(next_val).strip()
                                            else:
                                                df_stocks.loc[mask, f'SellDate{j}'] = ""
                                        df_stocks.loc[mask, 'SellDate10'] = ""
                                        # 즉시 저장
                                        save_stocks(df_stocks)
                                        st.success("삭제되었습니다!")
                                        # 0.5초 대기
                                        time.sleep(0.5)
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
                                # BuyDate1~10 저장 (None인 날짜는 빈 값으로, 순서대로 저장)
                                buy_dates_to_save = [d for d in buy_date_inputs if d is not None]
                                for i in range(1, 11):
                                    if i <= len(buy_dates_to_save):
                                        df_stocks.loc[mask, f'BuyDate{i}'] = buy_dates_to_save[i-1].strftime("%Y-%m-%d")
                                    else:
                                        df_stocks.loc[mask, f'BuyDate{i}'] = ""
                                # SellDate1~10 저장 (None인 날짜는 빈 값으로, 순서대로 저장)
                                sell_dates_to_save = [d for d in sell_date_inputs if d is not None]
                                for i in range(1, 11):
                                    if i <= len(sell_dates_to_save):
                                        df_stocks.loc[mask, f'SellDate{i}'] = sell_dates_to_save[i-1].strftime("%Y-%m-%d")
                                    else:
                                        df_stocks.loc[mask, f'SellDate{i}'] = ""
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
                    
                    # 매수일 표시 (네온 빨간색 화살표 - 위 방향) - 여러 개 표시
                    for i in range(1, 11):
                        buy_date_val = selected_row.get(f'BuyDate{i}', '')
                        if pd.notna(buy_date_val) and str(buy_date_val).strip() != "":
                            buy_dt = parse_date_safe(buy_date_val)
                            if buy_dt is not None:
                                try:
                                    if len(stock_data.index) > 0:
                                        trading_date = find_trading_date(buy_dt, stock_data.index)
                                        if trading_date is not None and trading_date in stock_data.index:
                                            price = stock_data.loc[trading_date, 'Low']
                                            # 가격 범위 계산 (텍스트 위치)
                                            price_range = stock_data['High'].max() - stock_data['Low'].min()
                                            offset = price_range * 0.01  # 가격 범위의 1%만큼 아래로
                                            text_y = price - offset  # 텍스트 위치
                                            text_label = "🔴 매수" if i == 1 else f"🔴 매수{i}"
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
                    
                    # 매도일 표시 (네온 하늘색 화살표 - 아래 방향) - 여러 개 표시
                    for i in range(1, 11):
                        sell_date_val = selected_row.get(f'SellDate{i}', '')
                        if pd.notna(sell_date_val) and str(sell_date_val).strip() != "":
                            sell_dt = parse_date_safe(sell_date_val)
                            if sell_dt is not None:
                                try:
                                    if len(stock_data.index) > 0:
                                        trading_date = find_trading_date(sell_dt, stock_data.index)
                                        if trading_date is not None and trading_date in stock_data.index:
                                            price = stock_data.loc[trading_date, 'High']
                                            # 가격 범위 계산 (텍스트 위치)
                                            price_range = stock_data['High'].max() - stock_data['Low'].min()
                                            offset = price_range * 0.01  # 가격 범위의 1%만큼 위로
                                            text_y = price + offset  # 텍스트 위치
                                            sell_dates.append(trading_date)
                                            sell_prices.append(price)
                                            text_label = "🔵 매도" if i == 1 else f"🔵 매도{i}"
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
    
    # JSON 파싱
    if not df_split.empty:
        if 'BuyTransactions' in df_split.columns:
            df_split['BuyTransactions'] = df_split['BuyTransactions'].apply(
                lambda x: json.loads(x) if isinstance(x, str) and x and x != '[]' else []
            )
        if 'SellTransactions' in df_split.columns:
            df_split['SellTransactions'] = df_split['SellTransactions'].apply(
                lambda x: json.loads(x) if isinstance(x, str) and x and x != '[]' else []
            )
    
    # ==========================================
    # 1. 포트폴리오 요약
    # ==========================================
    st.subheader("📊 포트폴리오 요약")
    
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
            
            max_investment = stock.get('MarketCap', 0) / 10000
            progress = (current_invested / max_investment * 100) if max_investment > 0 else 0
            
            portfolio_data.append({
                'id': stock.get('ID', ''),
                'name': stock.get('Name', ''),
                'totalInvested': current_invested,
                'progress': progress,
                'maxInvestment': max_investment
            })
            
            total_invested += current_invested
            total_budget += max_investment
        
        overall_progress = (total_invested / total_budget * 100) if total_budget > 0 else 0
        
        # 요약 메트릭
        col1, col2, col3 = st.columns(3)
        col1.metric("총 예산", f"{total_budget:,.0f}원")
        col2.metric("총 매입금액", f"{total_invested:,.0f}원")
        col3.metric("진행률", f"{overall_progress:.2f}%")
        
        # 도넛 차트
        if total_invested > 0:
            colors = px.colors.qualitative.Plotly
            chart_df = pd.DataFrame(portfolio_data)
            chart_df = chart_df[chart_df['totalInvested'] > 0].sort_values('totalInvested', ascending=False)
            
            if not chart_df.empty:
                fig_donut = px.pie(
                    chart_df,
                    values='totalInvested',
                    names='name',
                    hole=0.4,
                    color_discrete_sequence=colors
                )
                fig_donut.update_layout(
                    title="전체 총 매입금액",
                    showlegend=True,
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    height=400
                )
                fig_donut.update_traces(textinfo='percent+label', textposition='inside')
                st.plotly_chart(fig_donut, use_container_width=True)
        
        # 포트폴리오 테이블
        if portfolio_data:
            display_df = pd.DataFrame(portfolio_data)
            display_df = display_df.sort_values('totalInvested', ascending=False)
            display_df['percentage'] = (display_df['totalInvested'] / total_invested * 100) if total_invested > 0 else 0
            
            st.dataframe(
                display_df[['name', 'totalInvested', 'progress', 'percentage']].rename(columns={
                    'name': '종목명',
                    'totalInvested': '현재 매입금액',
                    'progress': '매수 진행률 (%)',
                    'percentage': '비중 (%)'
                }).style.format({
                    '현재 매입금액': '{:,.0f}',
                    '매수 진행률 (%)': '{:.2f}',
                    '비중 (%)': '{:.1f}'
                }),
                use_container_width=True
            )
    
    st.divider()
    
    # ==========================================
    # 2. 데이터 관리
    # ==========================================
    st.subheader("📁 데이터 관리")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ 데이터 초기화", type="secondary", key="reset_split_data"):
            if st.session_state.get('confirm_reset_split', False):
                df_split = pd.DataFrame(columns=["ID", "Name", "MarketCap", "Installments", "BuyTransactions", "SellTransactions"])
                save_split_purchase_data(df_split)
                st.success("데이터가 초기화되었습니다!")
                st.session_state['confirm_reset_split'] = False
                st.rerun()
            else:
                st.session_state['confirm_reset_split'] = True
                st.warning("⚠️ 다시 클릭하면 모든 데이터가 삭제됩니다!")
    
    st.divider()
    
    # ==========================================
    # 3. 새 종목 추가
    # ==========================================
    with st.expander("➕ 새 종목 추가", expanded=False):
        with st.form("add_split_stock_form"):
            name = st.text_input("종목명", placeholder="예: 삼성전자")
            market_cap = st.number_input("시가총액 (억원)", min_value=0, step=1000, placeholder="예: 5000000")
            installments = st.number_input("분할 횟수", min_value=1, value=3)
            
            if st.form_submit_button("계획 추가"):
                if name and market_cap > 0:
                    new_id = f"{datetime.now().timestamp()}-{len(df_split)}"
                    new_row = {
                        "ID": new_id,
                        "Name": name,
                        "MarketCap": market_cap * 100000000,  # 억원을 원으로 변환
                        "Installments": int(installments),
                        "BuyTransactions": json.dumps([]),
                        "SellTransactions": json.dumps([])
                    }
                    df_split = pd.concat([df_split, pd.DataFrame([new_row])], ignore_index=True)
                    save_split_purchase_data(df_split)
                    st.success(f"{name} 종목이 추가되었습니다!")
                    st.rerun()
                else:
                    st.error("종목명과 시가총액을 입력해주세요.")
    
    st.divider()
    
    # ==========================================
    # 4. 종목별 카드 표시
    # ==========================================
    if not df_split.empty:
        st.subheader("📦 종목별 상세 관리")
        
        for idx, stock in df_split.iterrows():
            stock_id = stock.get('ID', '')
            stock_name = stock.get('Name', '')
            market_cap = stock.get('MarketCap', 0)
            installments = stock.get('Installments', 3)
            buy_txs = stock.get('BuyTransactions', []) if isinstance(stock.get('BuyTransactions'), list) else []
            sell_txs = stock.get('SellTransactions', []) if isinstance(stock.get('SellTransactions'), list) else []
            
            # 거래 데이터 파싱
            if isinstance(buy_txs, str):
                try:
                    buy_txs = json.loads(buy_txs) if buy_txs and buy_txs != '[]' else []
                except:
                    buy_txs = []
            if isinstance(sell_txs, str):
                try:
                    sell_txs = json.loads(sell_txs) if sell_txs and sell_txs != '[]' else []
                except:
                    sell_txs = []
            
            max_investment = market_cap / 10000
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
            
            # 종목 카드
            with st.expander(f"📊 {stock_name}", expanded=False):
                # 요약 정보
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("최대 매수 가능액", f"{max_investment:,.0f}원")
                col2.metric("총 매입금액", f"{current_invested:,.0f}원")
                col3.metric("매입 평단가", f"{avg_price:,.0f}원")
                col4.metric("보유 수량", f"{current_qty:,} 주")
                col5.metric("분할 횟수", f"{installments}회")
                
                # 진행률
                st.progress(progress / 100)
                col_prog1, col_prog2 = st.columns(2)
                col_prog1.write(f"**매수 진행률: {progress:.2f}%**")
                col_prog2.write(f"**총 실현손익: {total_realized_profit:,.0f}원**")
                
                st.divider()
                
                # 매수 계획 및 기록
                col_buy, col_sell = st.columns(2)
                
                with col_buy:
                    st.subheader("매수 계획 및 기록")
                    
                    # 매수 테이블
                    buy_data = []
                    for i in range(installments):
                        tx = buy_txs[i] if i < len(buy_txs) else None
                        estimated_qty = int(amount_per_installment / tx.get('price', 1)) if tx and tx.get('price', 0) > 0 else 0
                        buy_data.append({
                            '회차': i + 1,
                            '날짜': tx.get('date', '') if tx else '',
                            '목표액': f"{amount_per_installment:,.0f}원",
                            '매수가': tx.get('price', '') if tx else '',
                            '예상': f"{estimated_qty:,}" if estimated_qty > 0 else '-',
                            '매수량': tx.get('quantity', '') if tx else ''
                        })
                    
                    buy_df = pd.DataFrame(buy_data)
                    st.dataframe(buy_df, use_container_width=True, hide_index=True)
                    
                    # 매수 기록 입력
                    with st.form(f"buy_form_{stock_id}"):
                        st.caption(f"{stock_name} 매수 기록")
                        buy_round = st.number_input("회차", min_value=1, max_value=installments, value=1, key=f"buy_round_{stock_id}")
                        buy_date = st.date_input("날짜", datetime.now(), key=f"buy_date_{stock_id}")
                        buy_price = st.number_input("매수가 (원)", min_value=0, step=100, key=f"buy_price_{stock_id}")
                        buy_qty = st.number_input("매수량 (주)", min_value=1, step=1, key=f"buy_qty_{stock_id}")
                        
                        if st.form_submit_button("기록"):
                            # buy_txs 리스트 확장
                            while len(buy_txs) < installments:
                                buy_txs.append(None)
                            
                            buy_txs[buy_round - 1] = {
                                'date': str(buy_date),
                                'price': float(buy_price),
                                'quantity': int(buy_qty)
                            }
                            
                            df_split.at[idx, 'BuyTransactions'] = json.dumps(buy_txs)
                            save_split_purchase_data(df_split)
                            st.success("매수 기록이 저장되었습니다!")
                            st.rerun()
                
                with col_sell:
                    st.subheader("분할 매도 기록")
                    
                    # 매도 기록 입력
                    with st.form(f"sell_form_{stock_id}"):
                        st.caption(f"{stock_name} 매도 기록")
                        sell_date = st.date_input("날짜", datetime.now(), key=f"sell_date_{stock_id}")
                        sell_price = st.number_input("매도가 (원)", min_value=0, step=100, key=f"sell_price_{stock_id}")
                        sell_qty = st.number_input("매도 수량 (주)", min_value=1, step=1, key=f"sell_qty_{stock_id}")
                        
                        if st.form_submit_button("추가"):
                            new_sell = {
                                'id': f"{datetime.now().timestamp()}",
                                'date': str(sell_date),
                                'price': float(sell_price),
                                'quantity': int(sell_qty)
                            }
                            sell_txs.append(new_sell)
                            df_split.at[idx, 'SellTransactions'] = json.dumps(sell_txs)
                            save_split_purchase_data(df_split)
                            st.success("매도 기록이 저장되었습니다!")
                            st.rerun()
                    
                    # 매도 테이블
                    if sell_txs:
                        sell_data = []
                        for i, tx in enumerate(sell_txs):
                            if isinstance(tx, dict):
                                profit = (tx.get('price', 0) - avg_price) * tx.get('quantity', 0) if avg_price > 0 else 0
                                yield_pct = ((tx.get('price', 0) - avg_price) / avg_price * 100) if avg_price > 0 else 0
                                
                                sell_data.append({
                                    '회차': i + 1,
                                    '날짜': tx.get('date', ''),
                                    '매도가': f"{tx.get('price', 0):,.0f}",
                                    '수량': tx.get('quantity', 0),
                                    '수익률': f"{yield_pct:.2f}%",
                                    '수익금': f"{profit:,.0f}"
                                })
                        
                        if sell_data:
                            sell_df = pd.DataFrame(sell_data)
                            st.dataframe(sell_df, use_container_width=True, hide_index=True)
                            
                            # 삭제 버튼
                            for i, tx in enumerate(sell_txs):
                                if st.button(f"🗑️ 삭제", key=f"delete_sell_{stock_id}_{i}"):
                                    sell_txs.pop(i)
                                    df_split.at[idx, 'SellTransactions'] = json.dumps(sell_txs)
                                    save_split_purchase_data(df_split)
                                    st.rerun()
                    else:
                        st.info("매도 기록이 없습니다.")
                
                # 종목 삭제
                if st.button(f"🗑️ {stock_name} 삭제", key=f"delete_stock_{stock_id}", type="secondary"):
                    df_split = df_split.drop(idx).reset_index(drop=True)
                    save_split_purchase_data(df_split)
                    st.success(f"{stock_name}이(가) 삭제되었습니다!")
                    st.rerun()
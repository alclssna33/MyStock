import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import os
import json
import time
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# 1. 페이지 설정 및 CSS 스타일
# ==========================================
st.set_page_config(
    page_title="나만의 주식 통합 관리",
    page_icon="📈",
    layout="wide"
)

# 모던 핀테크 스타일 CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700&display=swap');
    
    /* === 전체 앱 배경 === */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        font-family: 'Pretendard', sans-serif;
        color: #FFFFFF !important;
    }
    
    /* === 기본 텍스트 색상 === */
    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #FFFFFF;
    }
    
    /* === 사이드바 배경색 강제 변경 (중요) === */
    section[data-testid="stSidebar"] {
        background-color: #1a1a2e !important;
        color: #FFFFFF !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    
    /* 사이드바 입력 필드 예외 처리 (검은 글씨) */
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
    }
    
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div * {
        color: #000000 !important;
    }
    
    section[data-testid="stSidebar"] div[data-baseweb="calendar"] {
        background-color: #FFFFFF !important;
    }
    
    section[data-testid="stSidebar"] div[data-baseweb="calendar"] * {
        color: #000000 !important;
    }
    
    /* === 입력 필드 및 선택박스 스타일 === */
    input, textarea, select, div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 5px;
    }
    
    /* 드롭다운 메뉴 텍스트 블랙 강제 */
    div[data-baseweb="popover"] *,
    div[data-baseweb="menu"] *,
    ul[data-baseweb="menu"] * {
        color: #000000 !important;
    }
    
    /* === 탭 스타일 === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(255,255,255,0.05);
        padding: 10px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 5px;
        color: #aaaaaa;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #6366f1 !important;
        color: white !important;
        font-weight: bold;
    }
    
    /* === 메트릭 박스 === */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    div[data-testid="stMetric"] label {
        color: #cfcfcf !important;
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 700;
    }
    
    /* === 버튼 스타일 === */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: white !important;
        border: none;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    .stButton > button p {
        color: #FFFFFF !important;
    }
    
    /* === 카드 스타일 === */
    .stock-card {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    .stock-card h3 {
        color: #FFFFFF;
        margin-bottom: 15px;
    }
    
    .stock-card .metric-row {
        display: flex;
        gap: 15px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Google Sheets 연결 설정
# ==========================================
SPREADSHEET_NAME = "Integrated_Stock_DB"
SCOPE = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

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

def init_google_sheet():
    """Google Sheets 스프레드시트를 초기화합니다."""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        return spreadsheet
    except gspread.SpreadsheetNotFound:
        st.error(f"❌ '{SPREADSHEET_NAME}' 스프레드시트를 찾을 수 없습니다.\n\n"
                "구글 드라이브에 파일이 있는지 확인해주세요.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Google Sheets 초기화 실패: {str(e)}")
        st.stop()

# ==========================================
# 3. 데이터 로드 및 저장 함수
# ==========================================

@st.cache_data(ttl=60)  # 1분 캐싱
def load_data():
    """Stocks와 Transactions 데이터를 모두 로드합니다."""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        
        # Stocks 탭 로드
        try:
            ws_stocks = spreadsheet.worksheet("Stocks")
            stocks_data = ws_stocks.get_all_records()
            df_stocks = pd.DataFrame(stocks_data)
            
            # 필수 컬럼 확인 및 추가
            required_cols = ["Symbol", "Name", "Category", "Strategy", "TargetAmount", "PlanCount", "InterestDate", "Note"]
            if df_stocks.empty:
                df_stocks = pd.DataFrame(columns=required_cols)
            else:
                # 누락된 컬럼 추가
                for col in required_cols:
                    if col not in df_stocks.columns:
                        df_stocks[col] = ""
        except gspread.WorksheetNotFound:
            # 워크시트가 없으면 생성
            ws_stocks = spreadsheet.add_worksheet(title="Stocks", rows=1000, cols=20)
            headers = ["Symbol", "Name", "Category", "Strategy", "TargetAmount", "PlanCount", "InterestDate", "Note"]
            ws_stocks.append_row(headers)
            df_stocks = pd.DataFrame(columns=headers)
        except Exception as e:
            st.warning(f"Stocks 시트 로드 중 오류: {e}")
            df_stocks = pd.DataFrame(columns=["Symbol", "Name", "Category", "Strategy", "TargetAmount", "PlanCount", "InterestDate", "Note"])

        # Transactions 탭 로드
        try:
            ws_trans = spreadsheet.worksheet("Transactions")
            trans_data = ws_trans.get_all_records()
            df_trans = pd.DataFrame(trans_data)
            
            # 필수 컬럼 확인 및 추가
            required_cols = ["Date", "Symbol", "Type", "Price", "Quantity", "Round", "Note"]
            if df_trans.empty:
                df_trans = pd.DataFrame(columns=required_cols)
            else:
                # 누락된 컬럼 추가
                for col in required_cols:
                    if col not in df_trans.columns:
                        df_trans[col] = ""
        except gspread.WorksheetNotFound:
            # 워크시트가 없으면 생성
            ws_trans = spreadsheet.add_worksheet(title="Transactions", rows=1000, cols=20)
            headers = ["Date", "Symbol", "Type", "Price", "Quantity", "Round", "Note"]
            ws_trans.append_row(headers)
            df_trans = pd.DataFrame(columns=headers)
        except Exception as e:
            st.warning(f"Transactions 시트 로드 중 오류: {e}")
            df_trans = pd.DataFrame(columns=["Date", "Symbol", "Type", "Price", "Quantity", "Round", "Note"])
        
        return df_stocks, df_trans
    except Exception as e:
        st.error(f"❌ 데이터 로드 실패: {str(e)}")
        # 빈 DataFrame 반환
        df_stocks = pd.DataFrame(columns=["Symbol", "Name", "Category", "Strategy", "TargetAmount", "PlanCount", "InterestDate", "Note"])
        df_trans = pd.DataFrame(columns=["Date", "Symbol", "Type", "Price", "Quantity", "Round", "Note"])
        return df_stocks, df_trans

def save_stocks(df_stocks):
    """Stocks 시트에 데이터를 저장합니다."""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        ws_stocks = spreadsheet.worksheet("Stocks")
        
        # 빈 값 처리
        df_stocks = df_stocks.fillna("")
        
        # 헤더 포함 전체 데이터 준비
        values = [df_stocks.columns.tolist()] + df_stocks.values.tolist()
        
        # 기존 데이터 지우고 새 데이터 쓰기
        ws_stocks.clear()
        ws_stocks.update(values, value_input_option='USER_ENTERED')
        
        # 캐시 무효화
        load_data.clear()
    except Exception as e:
        st.error(f"❌ Stocks 데이터 저장 실패: {str(e)}")
        raise

def add_stock_to_db(symbol, name, strategy, target_amt, plan_count, note):
    """Stocks 시트에 새 종목 추가 (관심종목 등록)"""
    try:
        df_stocks, _ = load_data()
        
        # 중복 체크
        symbol_normalized = str(symbol).strip().upper()
        if not df_stocks.empty and 'Symbol' in df_stocks.columns:
            existing_symbols = df_stocks['Symbol'].astype(str).str.strip().str.upper()
            if symbol_normalized in existing_symbols.values:
                st.error("이미 등록된 종목입니다.")
                return False
        
        # 새 행 추가
        new_row = {
            "Symbol": symbol_normalized,
            "Name": str(name).strip(),
            "Category": "Interest",
            "Strategy": str(strategy),
            "TargetAmount": float(target_amt) if target_amt else 0,
            "PlanCount": int(plan_count) if plan_count else 0,
            "InterestDate": str(datetime.now().date()),
            "Note": str(note).strip() if note else ""
        }
        
        df_stocks = pd.concat([df_stocks, pd.DataFrame([new_row])], ignore_index=True)
        save_stocks(df_stocks)
        return True
    except Exception as e:
        st.error(f"종목 추가 실패: {str(e)}")
        return False

def add_transaction_to_db(date, symbol, t_type, price, qty, round_num, note):
    """Transactions 시트에 거래 기록 추가 및 Category 자동 업데이트"""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open(SPREADSHEET_NAME)
        
        # 1. 거래 내역 추가
        ws_trans = spreadsheet.worksheet("Transactions")
        ws_trans.append_row([
            str(date),
            str(symbol).strip().upper(),
            str(t_type),
            float(price),
            int(qty),
            int(round_num),
            str(note).strip() if note else ""
        ])
        
        # 2. 첫 매수(BUY)인 경우, Stocks의 Category를 'Holding'으로 자동 변경
        if t_type == "BUY":
            try:
                df_stocks, _ = load_data()
                symbol_normalized = str(symbol).strip().upper()
                
                if not df_stocks.empty and 'Symbol' in df_stocks.columns:
                    mask = df_stocks['Symbol'].astype(str).str.strip().str.upper() == symbol_normalized
                    if mask.any():
                        # Category가 'Interest'인 경우에만 'Holding'으로 변경
                        if 'Category' in df_stocks.columns:
                            df_stocks.loc[mask, 'Category'] = 'Holding'
                            save_stocks(df_stocks)
            except Exception as e:
                st.warning(f"Category 자동 업데이트 실패: {e}")
        
        # 캐시 무효화
        load_data.clear()
        return True
    except Exception as e:
        st.error(f"거래 기록 추가 실패: {str(e)}")
        return False

# ==========================================
# 4. 포트폴리오 계산 로직
# ==========================================

@st.cache_data(ttl=300)  # 5분 캐싱
def calculate_portfolio(df_stocks, df_trans):
    """Transactions 데이터를 기반으로 포트폴리오를 계산합니다."""
    portfolio = []
    
    if df_stocks.empty:
        return pd.DataFrame()

    for _, stock in df_stocks.iterrows():
        try:
            symbol = str(stock['Symbol']).strip()
            name = str(stock['Name']).strip()
            strategy = str(stock.get('Strategy', 'Long')).strip()
            category = str(stock.get('Category', 'Interest')).strip()
            target_amt = float(str(stock.get('TargetAmount', 0)).replace(',', '')) if stock.get('TargetAmount') else 0
            
            # 해당 종목의 거래 내역 필터링
            if not df_trans.empty and 'Symbol' in df_trans.columns:
                txs = df_trans[df_trans['Symbol'].astype(str).str.strip().str.upper() == symbol.upper()]
            else:
                txs = pd.DataFrame()

            total_qty = 0
            total_cost = 0
            realized_profit = 0
            
            if not txs.empty:
                for _, tx in txs.iterrows():
                    try:
                        qty = int(float(str(tx['Quantity']).replace(',', '')))
                        price = float(str(tx['Price']).replace(',', ''))
                        t_type = str(tx['Type']).strip().upper()
                        
                        if t_type == 'BUY':
                            total_cost += price * qty
                            total_qty += qty
                        elif t_type == 'SELL':
                            if total_qty > 0:
                                avg_price = total_cost / total_qty
                                profit = (price - avg_price) * qty
                                realized_profit += profit
                                total_cost -= avg_price * qty
                                total_qty -= qty
                    except Exception as e:
                        continue

            avg_price = total_cost / total_qty if total_qty > 0 else 0
            
            # 현재가 조회
            current_price = avg_price  # 기본값
            try:
                ticker = yf.Ticker(symbol)
                todays_data = ticker.history(period='1d')
                if not todays_data.empty:
                    current_price = float(todays_data['Close'].iloc[-1])
            except Exception:
                pass

            current_val = current_price * total_qty
            unrealized_profit = current_val - total_cost
            return_rate = ((current_price - avg_price) / avg_price * 100) if avg_price > 0 else 0

            portfolio.append({
                "Symbol": symbol,
                "Name": name,
                "Strategy": strategy,
                "Category": category,
                "Holdings": total_qty,
                "AvgPrice": avg_price,
                "CurrentPrice": current_price,
                "TotalInvested": total_cost,
                "CurrentValue": current_val,
                "ReturnRate": return_rate,
                "UnrealizedProfit": unrealized_profit,
                "RealizedProfit": realized_profit,
                "TargetAmount": target_amt
            })
        except Exception as e:
            continue

    return pd.DataFrame(portfolio)

# ==========================================
# 5. 주가 데이터 가져오기 (캐싱)
# ==========================================

@st.cache_data(ttl=3600)  # 1시간 캐싱
def get_stock_history(symbol):
    """yfinance를 사용하여 주가 데이터를 가져옵니다."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        
        # 타임존 정보 제거
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # 인덱스를 날짜만 남기고 시간 정보 제거
        df.index = pd.to_datetime(df.index).normalize()
        
        return df
    except Exception as e:
        return None

# ==========================================
# 6. 메인 앱 시작
# ==========================================

# 초기화
init_google_sheet()

# 데이터 로드
df_stocks, df_trans = load_data()
df_portfolio = calculate_portfolio(df_stocks, df_trans)

# ==========================================
# 7. 사이드바 (공통 입력 영역)
# ==========================================

with st.sidebar:
    st.header("⚙️ 설정 및 입력")
    
    # 관심 종목 등록
    with st.expander("➕ 관심 종목 등록 (Stocks)", expanded=False):
        with st.form("add_stock_form"):
            st.caption("새로운 종목을 마스터 DB에 등록합니다.")
            new_symbol = st.text_input("티커 (예: 005930.KS)", key="new_symbol")
            new_name = st.text_input("종목명 (예: 삼성전자)", key="new_name")
            new_strategy = st.selectbox("투자 전략", ["Long", "Short"], key="new_strategy")
            new_target = st.number_input("목표 투자금 (원)", min_value=0, step=100000, key="new_target")
            new_plan = st.number_input("분할 계획 (회)", value=3, min_value=1, key="new_plan")
            new_note = st.text_input("메모", key="new_note")
            
            if st.form_submit_button("관심종목 등록"):
                if new_symbol and new_name:
                    if add_stock_to_db(new_symbol, new_name, new_strategy, new_target, new_plan, new_note):
                        st.success(f"{new_name} 등록 완료!")
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.error("티커와 종목명은 필수입니다.")
    
    st.divider()
    
    # 매매 기록 입력
    with st.expander("💰 매매 기록 남기기 (Transactions)", expanded=True):
        with st.form("add_trans_form"):
            st.caption("실제 거래 내역을 가계부처럼 기록합니다.")
            
            # 종목 선택
            if not df_portfolio.empty:
                tr_options = [f"{row['Name']} ({row['Symbol']})" for _, row in df_portfolio.iterrows()]
                tr_sel = st.selectbox("종목", tr_options, key="tr_symbol_select")
                tr_symbol = tr_sel.split("(")[1].replace(")", "").strip()
            else:
                tr_symbol = st.text_input("티커 직접 입력", key="tr_symbol_input")
            
            tr_date = st.date_input("거래일", datetime.now(), key="tr_date")
            tr_type = st.selectbox("유형", ["BUY", "SELL"], key="tr_type")
            tr_price = st.number_input("단가 (원)", min_value=0, step=100, key="tr_price")
            tr_qty = st.number_input("수량 (주)", min_value=1, step=1, key="tr_qty")
            tr_round = st.number_input("회차", min_value=1, value=1, key="tr_round")
            tr_note = st.text_input("비고 (예: 물타기)", key="tr_note")
            
            if st.form_submit_button("거래 기록 저장"):
                if tr_symbol:
                    if add_transaction_to_db(tr_date, tr_symbol, tr_type, tr_price, tr_qty, tr_round, tr_note):
                        st.success("저장되었습니다!")
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.error("티커를 입력해주세요.")

# ==========================================
# 8. 메인 탭 구성
# ==========================================

tab_tracker, tab_manager = st.tabs(["📈 주식 추적기", "💰 주식 관리 (포트폴리오)"])

# ==========================================
# 탭 1: 주식 추적기
# ==========================================

with tab_tracker:
    st.title("📈 주식 추적기")
    
    # 종목 선택
    if not df_portfolio.empty:
        options = [f"{row['Name']} ({row['Symbol']})" for _, row in df_portfolio.iterrows()]
        selected_option = st.selectbox("종목 선택", options, key="tracker_select")
        selected_symbol = selected_option.split("(")[1].replace(")", "").strip()
        
        # 선택된 종목 정보 가져오기
        selected_stock_info = df_portfolio[df_portfolio['Symbol'] == selected_symbol]
        
        if not selected_stock_info.empty:
            selected_stock_info = selected_stock_info.iloc[0]
            
            # 실시간 시세 정보 (메트릭)
            m_col1, m_col2, m_col3 = st.columns(3)
            curr_price = selected_stock_info['CurrentPrice']
            holdings = selected_stock_info['Holdings']
            unrealized = selected_stock_info['UnrealizedProfit']
            return_rate = selected_stock_info['ReturnRate']
            
            m_col1.metric("현재가", f"{curr_price:,.0f}원")
            m_col2.metric("보유 수량", f"{holdings:,} 주")
            m_col3.metric("평가 손익", f"{unrealized:,.0f}원", f"{return_rate:.2f}%")
            
            # 차트 그리기
            hist_df = get_stock_history(selected_symbol)
            
            if hist_df is not None and not hist_df.empty:
                fig = go.Figure()
                
                # 캔들 차트
                fig.add_trace(go.Candlestick(
                    x=hist_df.index,
                    open=hist_df['Open'],
                    high=hist_df['High'],
                    low=hist_df['Low'],
                    close=hist_df['Close'],
                    name="주가",
                    increasing_line_color='#ef4444',
                    decreasing_line_color='#3b82f6'
                ))
                
                # ★ 핵심: Transactions 데이터를 기반으로 매수/매도 마커 찍기
                if not df_trans.empty and 'Symbol' in df_trans.columns:
                    # 현재 종목의 거래 내역만 필터링
                    stock_txs = df_trans[df_trans['Symbol'].astype(str).str.strip().str.upper() == selected_symbol.upper()]
                    
                    # 매수 마커 (BUY) - 빨간 화살표
                    buys = stock_txs[stock_txs['Type'].astype(str).str.strip().str.upper() == 'BUY']
                    if not buys.empty:
                        buy_dates = pd.to_datetime(buys['Date'], errors='coerce')
                        buy_prices = pd.to_numeric(buys['Price'], errors='coerce')
                        buy_quantities = buys['Quantity'].astype(str)
                        
                        # 유효한 날짜와 가격만 필터링
                        valid_mask = buy_dates.notna() & buy_prices.notna()
                        if valid_mask.any():
                            fig.add_trace(go.Scatter(
                                x=buy_dates[valid_mask],
                                y=buy_prices[valid_mask],
                                mode='markers+text',
                                marker=dict(
                                    symbol='triangle-up',
                                    size=15,
                                    color='#ef4444',
                                    line=dict(width=2, color='white')
                                ),
                                text=['매수'] * valid_mask.sum(),
                                textposition='top center',
                                name='매수',
                                hovertemplate='매수: %{y:,.0f}원<br>수량: %{text}주<extra></extra>',
                                texttemplate='매수'
                            ))
                    
                    # 매도 마커 (SELL) - 파란 화살표
                    sells = stock_txs[stock_txs['Type'].astype(str).str.strip().str.upper() == 'SELL']
                    if not sells.empty:
                        sell_dates = pd.to_datetime(sells['Date'], errors='coerce')
                        sell_prices = pd.to_numeric(sells['Price'], errors='coerce')
                        sell_quantities = sells['Quantity'].astype(str)
                        
                        # 유효한 날짜와 가격만 필터링
                        valid_mask = sell_dates.notna() & sell_prices.notna()
                        if valid_mask.any():
                            fig.add_trace(go.Scatter(
                                x=sell_dates[valid_mask],
                                y=sell_prices[valid_mask],
                                mode='markers+text',
                                marker=dict(
                                    symbol='triangle-down',
                                    size=15,
                                    color='#3b82f6',
                                    line=dict(width=2, color='white')
                                ),
                                text=['매도'] * valid_mask.sum(),
                                textposition='bottom center',
                                name='매도',
                                hovertemplate='매도: %{y:,.0f}원<br>수량: %{text}주<extra></extra>',
                                texttemplate='매도'
                            ))

                fig.update_layout(
                    height=600,
                    xaxis_rangeslider_visible=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
                
                # 종목 메모 표시
                if not df_stocks.empty and 'Symbol' in df_stocks.columns:
                    stock_row = df_stocks[df_stocks['Symbol'].astype(str).str.strip().str.upper() == selected_symbol.upper()]
                    if not stock_row.empty and 'Note' in stock_row.columns:
                        note = stock_row.iloc[0]['Note']
                        if note and str(note).strip():
                            st.info(f"📝 메모: {note}")
            else:
                st.error("차트 데이터를 불러올 수 없습니다.")
        else:
            st.warning("선택한 종목 정보를 찾을 수 없습니다.")
    else:
        st.info("등록된 종목이 없습니다. 사이드바에서 추가해주세요.")

# ==========================================
# 탭 2: 주식 관리 (포트폴리오)
# ==========================================

with tab_manager:
    st.title("💰 포트폴리오 현황")
    
    # 전략 필터 (Long / Short)
    strategy_filter = st.radio("투자 전략 필터", ["전체", "Long (중장기)", "Short (단타)"], horizontal=True, key="strategy_filter")
    
    # 필터링된 데이터프레임
    if strategy_filter == "Long (중장기)":
        filtered_pf = df_portfolio[df_portfolio['Strategy'] == 'Long']
    elif strategy_filter == "Short (단타)":
        filtered_pf = df_portfolio[df_portfolio['Strategy'] == 'Short']
    else:
        filtered_pf = df_portfolio

    # 보유 중인 종목만 보기 (옵션)
    show_only_holding = st.checkbox("보유 중인 종목만 보기", value=True, key="show_holding")
    if show_only_holding:
        filtered_pf = filtered_pf[filtered_pf['Holdings'] > 0]

    if not filtered_pf.empty:
        # 요약 메트릭
        total_invested = filtered_pf['TotalInvested'].sum()
        total_val = filtered_pf['CurrentValue'].sum()
        total_pf_profit = total_val - total_invested
        total_pf_roi = (total_pf_profit / total_invested * 100) if total_invested > 0 else 0
        total_realized = filtered_pf['RealizedProfit'].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("총 매입금액", f"{total_invested:,.0f}원")
        col2.metric("총 평가금액", f"{total_val:,.0f}원")
        col3.metric("총 평가손익", f"{total_pf_profit:,.0f}원", f"{total_pf_roi:.2f}%")
        col4.metric("실현 수익 (익절/손절)", f"{total_realized:,.0f}원", delta_color="off")
        
        st.divider()

        # 차트와 테이블
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.subheader("📊 자산 비중")
            if total_val > 0:
                fig_donut = px.pie(
                    filtered_pf,
                    values='CurrentValue',
                    names='Name',
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Plotly
                )
                fig_donut.update_layout(
                    showlegend=False,
                    margin=dict(t=0, b=0, l=0, r=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white')
                )
                fig_donut.update_traces(textinfo='percent+label', textposition='inside')
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info("자산이 없습니다.")

        with c2:
            st.subheader("📋 상세 보유 현황")
            # 보여줄 컬럼 선택 및 정렬
            display_cols = ['Name', 'Symbol', 'Strategy', 'Holdings', 'AvgPrice', 'CurrentPrice', 'ReturnRate', 'CurrentValue', 'RealizedProfit']
            display_df = filtered_pf[display_cols].copy().sort_values(by='CurrentValue', ascending=False)
            
            # 컬럼명 한글화
            display_df.columns = ['종목명', '티커', '전략', '보유수량', '평단가', '현재가', '수익률', '평가액', '실현손익']
            
            # 스타일링하여 표시
            styled_df = display_df.style.format({
                '보유수량': "{:,}",
                '평단가': "{:,.0f}",
                '현재가': "{:,.0f}",
                '평가액': "{:,.0f}",
                '실현손익': "{:,.0f}",
                '수익률': "{:.2f}%"
            })
            
            st.dataframe(styled_df, use_container_width=True, height=400)
    else:
        st.info("해당 조건의 종목이 없습니다.")
    
    st.divider()
    
    # ==========================================
    # 보유 종목 카드 형태로 표시 (각 카드에 거래 입력 폼 포함)
    # ==========================================
    if not filtered_pf.empty:
        st.subheader("📦 보유 종목 상세 관리")
        
        # 보유 중인 종목만 필터링
        holding_stocks = filtered_pf[filtered_pf['Holdings'] > 0].copy()
        
        if not holding_stocks.empty:
            # 보유 종목을 카드 형태로 반복 표시
            for idx, stock in holding_stocks.iterrows():
                symbol = stock['Symbol']
                name = stock['Name']
                holdings = stock['Holdings']
                avg_price = stock['AvgPrice']
                current_price = stock['CurrentPrice']
                current_value = stock['CurrentValue']
                unrealized_profit = stock['UnrealizedProfit']
                return_rate = stock['ReturnRate']
                realized_profit = stock['RealizedProfit']
                strategy = stock['Strategy']
                
                # 카드 컨테이너
                with st.container():
                    st.markdown(f"""
                    <div class="stock-card">
                        <h3>{name} ({symbol})</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 종목 요약 정보 (메트릭)
                    metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
                    metric_col1.metric("보유 수량", f"{holdings:,} 주")
                    metric_col2.metric("평단가", f"{avg_price:,.0f}원")
                    metric_col3.metric("현재가", f"{current_price:,.0f}원")
                    metric_col4.metric("평가 손익", f"{unrealized_profit:,.0f}원", f"{return_rate:.2f}%")
                    metric_col5.metric("실현 손익", f"{realized_profit:,.0f}원", delta_color="off")
                    
                    st.divider()
                    
                    # 거래 기록 입력 폼 (Expander)
                    with st.expander(f"📝 {name} 거래 기록 남기기", expanded=False):
                        with st.form(f"transaction_form_{symbol}_{idx}"):
                            st.caption(f"종목: {name} ({symbol}) - 티커가 자동으로 적용됩니다.")
                            
                            # 거래 정보 입력
                            trans_date = st.date_input("거래일", datetime.now(), key=f"trans_date_{symbol}_{idx}")
                            trans_type = st.selectbox("유형", ["BUY", "SELL"], key=f"trans_type_{symbol}_{idx}")
                            trans_price = st.number_input("단가 (원)", min_value=0, step=100, key=f"trans_price_{symbol}_{idx}")
                            trans_qty = st.number_input("수량 (주)", min_value=1, step=1, key=f"trans_qty_{symbol}_{idx}")
                            
                            # 회차 계산 (해당 종목의 기존 거래 내역 확인)
                            if not df_trans.empty and 'Symbol' in df_trans.columns:
                                stock_transactions = df_trans[df_trans['Symbol'].astype(str).str.strip().str.upper() == symbol.upper()]
                                if not stock_transactions.empty and 'Round' in stock_transactions.columns:
                                    max_round = stock_transactions['Round'].astype(int).max() if 'Round' in stock_transactions.columns else 0
                                    next_round = max_round + 1
                                else:
                                    next_round = 1
                            else:
                                next_round = 1
                            
                            trans_round = st.number_input("회차", min_value=1, value=next_round, key=f"trans_round_{symbol}_{idx}")
                            trans_note = st.text_input("비고 (예: 물타기)", key=f"trans_note_{symbol}_{idx}")
                            
                            if st.form_submit_button("💾 거래 기록 저장", key=f"save_trans_{symbol}_{idx}"):
                                if add_transaction_to_db(trans_date, symbol, trans_type, trans_price, trans_qty, trans_round, trans_note):
                                    st.success(f"{name} 거래 기록이 저장되었습니다!")
                                    time.sleep(0.5)
                                    st.rerun()
                    
                    # 해당 종목의 거래 내역 표시
                    if not df_trans.empty and 'Symbol' in df_trans.columns:
                        stock_ledger = df_trans[df_trans['Symbol'].astype(str).str.strip().str.upper() == symbol.upper()].copy()
                        if not stock_ledger.empty:
                            stock_ledger = stock_ledger.sort_values(by='Date', ascending=False)
                            with st.expander(f"📋 {name} 거래 내역 보기", expanded=False):
                                st.dataframe(stock_ledger, use_container_width=True)
                    
                    st.divider()
        else:
            st.info("보유 중인 종목이 없습니다.")
    else:
        st.info("등록된 종목이 없습니다.")

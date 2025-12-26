import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import os
import time
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. 페이지 및 스타일 설정 ---
st.set_page_config(
    page_title="나만의 주식 통합 관리",
    page_icon="📈",
    layout="wide"
)

# 모던 핀테크 스타일 CSS (기존 스타일 유지)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        font-family: 'Pretendard', sans-serif;
        color: #FFFFFF !important;
    }
    
    h1, h2, h3, h4, h5, h6, p, label, span, div { color: #FFFFFF; }
    
    /* 입력 필드 및 선택박스 스타일 */
    input, textarea, select, div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 5px;
    }
    /* 드롭다운 메뉴 텍스트 블랙 강제 */
    div[data-baseweb="popover"] *, div[data-baseweb="menu"] *, ul[data-baseweb="menu"] * {
        color: #000000 !important;
    }
    
    /* 탭 스타일 */
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

    /* 메트릭 박스 */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div[data-testid="stMetric"] label { color: #cfcfcf !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 700; }

    /* 버튼 스타일 */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: white !important;
        border: none;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 구글 시트 연결 설정 ---
SPREADSHEET_NAME = "Integrated_Stock_DB"  # 통합 DB 이름
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

@st.cache_resource
def get_google_sheets_client():
    try:
        if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
            creds_dict = dict(st.secrets['gcp_service_account'])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        elif os.path.exists("secrets.json"):
            creds = ServiceAccountCredentials.from_json_keyfile_name("secrets.json", SCOPE)
        else:
            st.error("❌ 인증 파일을 찾을 수 없습니다.")
            st.stop()
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ 구글 시트 연결 실패: {e}")
        st.stop()

def init_google_sheet():
    client = get_google_sheets_client()
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
    except gspread.SpreadsheetNotFound:
        st.error(f"❌ '{SPREADSHEET_NAME}' 스프레드시트를 찾을 수 없습니다. 구글 드라이브에 파일이 있는지 확인해주세요.")
        st.stop()
    return spreadsheet

# --- 3. 데이터 로드 및 저장 함수 ---

def load_data():
    """Stocks와 Transactions 데이터를 모두 로드합니다."""
    client = get_google_sheets_client()
    spreadsheet = client.open(SPREADSHEET_NAME)
    
    # Stocks 탭 로드
    try:
        ws_stocks = spreadsheet.worksheet("Stocks")
        stocks_data = ws_stocks.get_all_records()
        df_stocks = pd.DataFrame(stocks_data)
        # 필수 컬럼이 없으면 빈 DataFrame 처리
        if df_stocks.empty and 'Symbol' not in df_stocks.columns:
             df_stocks = pd.DataFrame(columns=["Symbol", "Name", "Category", "Strategy", "TargetAmount", "PlanCount", "InterestDate", "Note"])
    except:
        df_stocks = pd.DataFrame(columns=["Symbol", "Name", "Category", "Strategy", "TargetAmount", "PlanCount", "InterestDate", "Note"])

    # Transactions 탭 로드
    try:
        ws_trans = spreadsheet.worksheet("Transactions")
        trans_data = ws_trans.get_all_records()
        df_trans = pd.DataFrame(trans_data)
        if df_trans.empty and 'Symbol' not in df_trans.columns:
            df_trans = pd.DataFrame(columns=["Date", "Symbol", "Type", "Price", "Quantity", "Round", "Note"])
    except:
         df_trans = pd.DataFrame(columns=["Date", "Symbol", "Type", "Price", "Quantity", "Round", "Note"])
    
    return df_stocks, df_trans

def add_stock_to_db(symbol, name, strategy, target_amt, plan_count, note):
    """Stocks 시트에 새 종목 추가 (관심종목 등록)"""
    client = get_google_sheets_client()
    ws = client.open(SPREADSHEET_NAME).worksheet("Stocks")
    # Category는 기본적으로 'Interest'로 시작
    ws.append_row([symbol.upper(), name, "Interest", strategy, target_amt, plan_count, str(datetime.now().date()), note])
    st.cache_data.clear()

def add_transaction_to_db(date, symbol, t_type, price, qty, round_num, note):
    """Transactions 시트에 거래 기록 추가"""
    client = get_google_sheets_client()
    ss = client.open(SPREADSHEET_NAME)
    
    # 1. 거래 내역 추가
    ws_trans = ss.worksheet("Transactions")
    ws_trans.append_row([str(date), symbol.upper(), t_type, price, qty, round_num, note])
    
    # 2. 첫 매수(BUY)인 경우, Stocks의 Category를 'Holding'으로 자동 변경
    if t_type == "BUY":
        try:
            ws_stocks = ss.worksheet("Stocks")
            stocks_data = ws_stocks.get_all_records()
            df_stocks = pd.DataFrame(stocks_data)
            
            # 해당 Symbol이 Stocks에 있는지 확인
            mask = df_stocks['Symbol'] == symbol.upper()
            if mask.any():
                row_idx = df_stocks.index[mask][0] + 2 # 헤더(1) + 0-based index(1)
                # Category 열이 C열(3번째)이라고 가정 (구조에 따라 확인 필요)
                # 안전하게 findCell로 찾는 것이 좋으나 여기선 간단히 업데이트 로직 구현
                # Stocks 구조: Symbol, Name, Category, Strategy...
                ws_stocks.update_cell(row_idx, 3, "Holding") 
        except Exception as e:
            print(f"Category 업데이트 실패: {e}")

    st.cache_data.clear()

# --- 4. 포트폴리오 계산 로직 (React 앱 기능 이식) ---
def calculate_portfolio(df_stocks, df_trans):
    portfolio = []
    
    if df_stocks.empty:
        return pd.DataFrame()

    for _, stock in df_stocks.iterrows():
        symbol = str(stock['Symbol']).strip()
        name = stock['Name']
        strategy = stock.get('Strategy', 'Long') # 없으면 기본 Long
        category = stock.get('Category', 'Interest')
        target_amt = float(str(stock['TargetAmount']).replace(',','')) if stock['TargetAmount'] else 0
        
        # 해당 종목의 거래 내역 필터링
        if not df_trans.empty:
            txs = df_trans[df_trans['Symbol'].astype(str) == symbol]
        else:
            txs = pd.DataFrame()

        total_qty = 0
        total_cost = 0
        realized_profit = 0
        
        if not txs.empty:
            for _, tx in txs.iterrows():
                try:
                    qty = int(str(tx['Quantity']).replace(',',''))
                    price = float(str(tx['Price']).replace(',',''))
                    t_type = tx['Type']
                    
                    if t_type == 'BUY':
                        total_cost += price * qty
                        total_qty += qty
                    elif t_type == 'SELL':
                        if total_qty > 0:
                            avg_price = total_cost / total_qty
                            profit = (price - avg_price) * qty
                            realized_profit += profit
                            total_cost -= avg_price * qty # 평단가 유지 방식
                            total_qty -= qty
                except:
                    continue

        avg_price = total_cost / total_qty if total_qty > 0 else 0
        
        # 현재가 조회 (캐싱 적용 권장)
        current_price = avg_price # 기본값
        try:
            ticker = yf.Ticker(symbol)
            # 장중 데이터 가져오기 시도
            todays_data = ticker.history(period='1d')
            if not todays_data.empty:
                current_price = todays_data['Close'].iloc[-1]
        except:
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

    return pd.DataFrame(portfolio)

# 주가 데이터 가져오기 (캐싱)
@st.cache_data(ttl=3600)
def get_stock_history(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        return df
    except:
        return None

# --- 메인 앱 시작 ---
df_stocks, df_trans = load_data()
df_portfolio = calculate_portfolio(df_stocks, df_trans)

# 사이드바 공통 영역 (로그인/로그아웃 등 필요시 여기에)
with st.sidebar:
    st.header("⚙️ 설정 및 입력")
    # 여기서 입력 폼을 탭에 따라 다르게 보여줄 수도 있음
    
# 탭 구성: 기존 추적기(Chart) vs 주식 관리(Asset)
tab_tracker, tab_manager = st.tabs(["📈 주식 추적기", "💰 주식 관리 (포트폴리오)"])

# ==========================================
# 탭 1: 주식 추적기 (기존 기능 유지 + 마커 업그레이드)
# ==========================================
with tab_tracker:
    # 1. 상단 컨트롤 (종목 선택)
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # DB에 있는 종목 리스트업
        if not df_portfolio.empty:
            # 검색 편의를 위해 "이름 (티커)" 형식 사용
            options = [f"{row['Name']} ({row['Symbol']})" for _, row in df_portfolio.iterrows()]
            selected_option = st.selectbox("종목 선택", options, key="tracker_select")
            selected_symbol = selected_option.split("(")[1].replace(")", "")
            
            # 선택된 종목 정보 가져오기
            selected_stock_info = df_portfolio[df_portfolio['Symbol'] == selected_symbol].iloc[0]
        else:
            st.info("등록된 종목이 없습니다. 사이드바에서 추가해주세요.")
            selected_symbol = None

    # 2. 종목 추가 (사이드바에 배치)
    with st.sidebar:
        with st.expander("➕ 관심 종목 등록 (Stocks)", expanded=False):
            with st.form("add_stock_form"):
                st.caption("새로운 종목을 마스터 DB에 등록합니다.")
                new_symbol = st.text_input("티커 (예: 005930.KS)")
                new_name = st.text_input("종목명 (예: 삼성전자)")
                new_strategy = st.selectbox("투자 전략", ["Long", "Short"])
                new_target = st.number_input("목표 투자금 (원)", min_value=0, step=100000)
                new_plan = st.number_input("분할 계획 (회)", value=3)
                new_note = st.text_input("메모")
                
                if st.form_submit_button("관심종목 등록"):
                    if new_symbol and new_name:
                        add_stock_to_db(new_symbol, new_name, new_strategy, new_target, new_plan, new_note)
                        st.success(f"{new_name} 등록 완료!")
                        st.rerun()
                    else:
                        st.error("티커와 종목명은 필수입니다.")

    # 3. 차트 및 정보 표시
    if selected_symbol:
        st.subheader(f"{selected_stock_info['Name']} ({selected_symbol}) 차트 분석")
        
        # 실시간 시세 정보 (메트릭)
        m_col1, m_col2, m_col3 = st.columns(3)
        curr_price = selected_stock_info['CurrentPrice']
        prev_close = 0 # 전일 종가는 yfinance history에서 계산 필요하지만 여기선 생략 또는 추가 구현
        
        m_col1.metric("현재가", f"{curr_price:,.0f}원")
        m_col2.metric("보유 수량", f"{selected_stock_info['Holdings']:,} 주")
        m_col3.metric("평가 손익", f"{selected_stock_info['UnrealizedProfit']:,.0f}원", f"{selected_stock_info['ReturnRate']:.2f}%")

        # 차트 그리기
        hist_df = get_stock_history(selected_symbol)
        
        if hist_df is not None and not hist_df.empty:
            fig = go.Figure()
            
            # 캔들 차트
            fig.add_trace(go.Candlestick(
                x=hist_df.index,
                open=hist_df['Open'], high=hist_df['High'],
                low=hist_df['Low'], close=hist_df['Close'],
                name="주가",
                increasing_line_color='#ef4444', decreasing_line_color='#3b82f6'
            ))
            
            # ★ 핵심: Transactions 데이터를 기반으로 매수/매도 마커 찍기
            if not df_trans.empty:
                # 현재 종목의 거래 내역만 필터링
                stock_txs = df_trans[df_trans['Symbol'] == selected_symbol]
                
                # 매수 마커 (BUY)
                buys = stock_txs[stock_txs['Type'] == 'BUY']
                if not buys.empty:
                    fig.add_trace(go.Scatter(
                        x=pd.to_datetime(buys['Date']), 
                        y=buys['Price'],
                        mode='markers',
                        marker=dict(symbol='triangle-up', size=12, color='#ef4444', line=dict(width=1, color='white')),
                        name='매수',
                        hovertemplate='매수: %{y:,.0f}원<br>수량: %{text}주',
                        text=buys['Quantity']
                    ))
                
                # 매도 마커 (SELL)
                sells = stock_txs[stock_txs['Type'] == 'SELL']
                if not sells.empty:
                    fig.add_trace(go.Scatter(
                        x=pd.to_datetime(sells['Date']), 
                        y=sells['Price'],
                        mode='markers',
                        marker=dict(symbol='triangle-down', size=12, color='#3b82f6', line=dict(width=1, color='white')),
                        name='매도',
                        hovertemplate='매도: %{y:,.0f}원<br>수량: %{text}주',
                        text=sells['Quantity']
                    ))

            fig.update_layout(
                height=600,
                xaxis_rangeslider_visible=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 종목 메모 표시
            # Stocks 시트에 있는 Note 가져오기
            note = df_stocks[df_stocks['Symbol'] == selected_symbol]['Note'].values[0]
            if note:
                st.info(f"📝 메모: {note}")
        else:
            st.error("차트 데이터를 불러올 수 없습니다.")


# ==========================================
# 탭 2: 주식 관리 (포트폴리오 & 매매입력)
# ==========================================
with tab_manager:
    # 1. 매매 기록 입력 (사이드바 혹은 상단)
    with st.sidebar:
        st.divider()
        with st.expander("💰 매매 기록 남기기 (Transactions)", expanded=True):
            with st.form("add_trans_form"):
                st.caption("실제 거래 내역을 가계부처럼 기록합니다.")
                # 종목 선택 (티커 자동 입력)
                if not df_portfolio.empty:
                    tr_options = [f"{row['Name']} ({row['Symbol']})" for _, row in df_portfolio.iterrows()]
                    tr_sel = st.selectbox("종목", tr_options)
                    tr_symbol = tr_sel.split("(")[1].replace(")", "")
                else:
                    tr_symbol = st.text_input("티커 직접 입력")
                
                tr_date = st.date_input("거래일", datetime.now())
                tr_type = st.selectbox("유형", ["BUY", "SELL"])
                tr_price = st.number_input("단가 (원)", min_value=0, step=100)
                tr_qty = st.number_input("수량 (주)", min_value=1, step=1)
                tr_round = st.number_input("회차", min_value=1, value=1)
                tr_note = st.text_input("비고 (예: 물타기)")
                
                if st.form_submit_button("거래 기록 저장"):
                    add_transaction_to_db(tr_date, tr_symbol, tr_type, tr_price, tr_qty, tr_round, tr_note)
                    st.success("저장되었습니다!")
                    st.rerun()

    # 2. 필터링 및 요약 대시보드
    st.title("💰 포트폴리오 현황")
    
    # 전략 필터 (Long / Short)
    strategy_filter = st.radio("투자 전략 필터", ["전체", "Long (중장기)", "Short (단타)"], horizontal=True)
    
    # 필터링된 데이터프레임
    if strategy_filter == "Long (중장기)":
        filtered_pf = df_portfolio[df_portfolio['Strategy'] == 'Long']
    elif strategy_filter == "Short (단타)":
        filtered_pf = df_portfolio[df_portfolio['Strategy'] == 'Short']
    else:
        filtered_pf = df_portfolio

    # 보유 중인 종목만 보기 (옵션)
    show_only_holding = st.checkbox("보유 중인 종목만 보기", value=True)
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
                fig_donut = px.pie(filtered_pf, values='CurrentValue', names='Name', hole=0.4,
                                   color_discrete_sequence=px.colors.qualitative.Plotly)
                fig_donut.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), 
                                      paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
                fig_donut.update_traces(textinfo='percent+label', textposition='inside')
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info("자산이 없습니다.")

        with c2:
            st.subheader("📋 상세 보유 현황")
            # 보여줄 컬럼 선택 및 정렬
            display_cols = ['Name', 'Symbol', 'Strategy', 'Holdings', 'AvgPrice', 'CurrentPrice', 'ReturnRate', 'CurrentValue', 'RealizedProfit']
            display_df = filtered_pf[display_cols].sort_values(by='CurrentValue', ascending=False)
            
            # 컬럼명 한글화
            display_df.columns = ['종목명', '티커', '전략', '보유수량', '평단가', '현재가', '수익률', '평가액', '실현손익']
            
            # 스타일링하여 표시
            st.dataframe(
                display_df.style.format({
                    '보유수량': "{:,}",
                    '평단가': "{:,.0f}",
                    '현재가': "{:,.0f}",
                    '평가액': "{:,.0f}",
                    '실현손익': "{:,.0f}",
                    '수익률': "{:.2f}%"
                }).background_gradient(subset=['수익률'], cmap='RdYlGn', vmin=-10, vmax=10),
                use_container_width=True,
                height=400
            )

    else:
        st.info("해당 조건의 종목이 없습니다.")
    
    st.divider()
    
    # 3. 상세 거래 내역 (Ledger) 조회
    st.subheader("📝 종목별 거래 내역 조회")
    if not df_portfolio.empty:
        ledger_stock = st.selectbox("내역을 확인할 종목 선택", df_portfolio['Name'] + " (" + df_portfolio['Symbol'] + ")", key="ledger_select")
        ledger_symbol = ledger_stock.split("(")[1].replace(")", "")
        
        # Transactions에서 해당 종목 필터링
        if not df_trans.empty:
            my_ledger = df_trans[df_trans['Symbol'] == ledger_symbol].sort_values(by='Date', ascending=False)
            if not my_ledger.empty:
                st.dataframe(my_ledger, use_container_width=True)
            else:
                st.info("거래 내역이 없습니다.")
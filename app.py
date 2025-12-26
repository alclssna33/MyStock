import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import os
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import math

# --- 1. 페이지 및 스타일 설정 ---
st.set_page_config(
    page_title="주식 통합 관리 시스템",
    page_icon="📈",
    layout="wide"
)

# 다크모드 및 가독성 CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        font-family: 'Pretendard', sans-serif;
        color: #FFFFFF !important;
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #1a1a2e !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* 텍스트 색상 강제 지정 */
    h1, h2, h3, h4, h5, h6, p, label, span, div { color: #FFFFFF; }
    
    /* 입력 폼 스타일 (검은 글씨) */
    input, textarea, select, div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 5px;
    }
    /* 드롭다운 메뉴 텍스트 */
    div[data-baseweb="popover"] *, div[data-baseweb="menu"] * {
        color: #000000 !important;
    }
    
    /* 카드 스타일 컨테이너 */
    .stock-card {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(255,255,255,0.05);
        padding: 10px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 5px;
        color: #aaaaaa;
    }
    .stTabs [aria-selected="true"] {
        background-color: #6366f1 !important;
        color: white !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 구글 시트 연결 ---
SPREADSHEET_NAME = "Integrated_Stock_DB"
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
            st.error("❌ secrets.json 파일이 필요합니다.")
            st.stop()
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ 구글 시트 연결 오류: {e}")
        st.stop()

def init_google_sheet():
    client = get_google_sheets_client()
    try:
        return client.open(SPREADSHEET_NAME)
    except Exception as e:
        st.error(f"❌ '{SPREADSHEET_NAME}' 시트를 찾을 수 없습니다. ({e})")
        st.stop()

# --- 3. 데이터 로드/저장 로직 ---

def load_data():
    ss = init_google_sheet()
    
    # Stocks 로드
    try:
        ws_stocks = ss.worksheet("Stocks")
        df_stocks = pd.DataFrame(ws_stocks.get_all_records())
        # 필수 컬럼 체크 및 빈 DF 처리
        if df_stocks.empty and 'Symbol' not in df_stocks.columns:
            df_stocks = pd.DataFrame(columns=["Symbol", "Name", "Category", "Strategy", "TargetAmount", "PlanCount", "InterestDate", "Note"])
    except:
        df_stocks = pd.DataFrame(columns=["Symbol", "Name", "Category", "Strategy", "TargetAmount", "PlanCount", "InterestDate", "Note"])

    # Transactions 로드
    try:
        ws_trans = ss.worksheet("Transactions")
        df_trans = pd.DataFrame(ws_trans.get_all_records())
        if df_trans.empty and 'Symbol' not in df_trans.columns:
             df_trans = pd.DataFrame(columns=["Date", "Symbol", "Type", "Price", "Quantity", "Round", "Note"])
    except:
         df_trans = pd.DataFrame(columns=["Date", "Symbol", "Type", "Price", "Quantity", "Round", "Note"])
         
    return df_stocks, df_trans, ss

def add_stock_to_db(symbol, name, strategy, target_amt, plan_count, note):
    ss = init_google_sheet()
    ws = ss.worksheet("Stocks")
    ws.append_row([symbol.upper(), name, "Interest", strategy, target_amt, plan_count, str(datetime.now().date()), note])
    st.cache_data.clear()

def add_transaction_to_db(date, symbol, t_type, price, qty, round_num, note):
    ss = init_google_sheet()
    ws_trans = ss.worksheet("Transactions")
    ws_trans.append_row([str(date), symbol.upper(), t_type, price, qty, round_num, note])
    
    # 첫 매수 시 Stocks 상태 변경 (Interest -> Holding)
    if t_type == "BUY":
        try:
            ws_stocks = ss.worksheet("Stocks")
            stocks_data = ws_stocks.get_all_records()
            df_stocks = pd.DataFrame(stocks_data)
            mask = df_stocks['Symbol'] == symbol.upper()
            if mask.any():
                # gspread는 1-based index, 헤더 제외하고...
                # 안전하게 cell find 사용
                cell = ws_stocks.find(symbol.upper())
                if cell:
                    # Category 열이 3번째라고 가정 (C열)
                    ws_stocks.update_cell(cell.row, 3, "Holding")
        except:
            pass
    st.cache_data.clear()

def update_stock_plan_count(symbol, new_count):
    ss = init_google_sheet()
    ws = ss.worksheet("Stocks")
    try:
        cell = ws.find(symbol.upper())
        if cell:
            # PlanCount는 6번째 열(F열)이라고 가정 (구조: Symbol, Name, Category, Strategy, Target, PlanCount...)
            ws.update_cell(cell.row, 6, new_count)
            st.cache_data.clear()
            return True
    except:
        return False
    return False

# --- 4. 포트폴리오 계산 로직 ---
def calculate_portfolio(df_stocks, df_trans):
    portfolio = []
    if df_stocks.empty: return pd.DataFrame()

    for _, stock in df_stocks.iterrows():
        symbol = str(stock['Symbol']).strip()
        name = stock['Name']
        strategy = stock.get('Strategy', 'Long')
        
        # 숫자형 데이터 안전 변환
        try: target_amt = float(str(stock.get('TargetAmount', 0)).replace(',',''))
        except: target_amt = 0
        try: plan_count = int(str(stock.get('PlanCount', 3)).replace(',',''))
        except: plan_count = 3
        
        # 거래 내역 필터링
        if not df_trans.empty:
            txs = df_trans[df_trans['Symbol'].astype(str) == symbol]
        else:
            txs = pd.DataFrame()

        total_qty = 0
        total_cost = 0
        buy_count = 0 # 매수 횟수 (회차 계산용)
        
        if not txs.empty:
            for _, tx in txs.iterrows():
                try:
                    qty = int(str(tx['Quantity']).replace(',',''))
                    price = float(str(tx['Price']).replace(',',''))
                    t_type = tx['Type']
                    
                    if t_type == 'BUY':
                        total_cost += price * qty
                        total_qty += qty
                        buy_count += 1
                    elif t_type == 'SELL':
                        if total_qty > 0:
                            avg_price = total_cost / total_qty
                            total_cost -= avg_price * qty
                            total_qty -= qty
                except:
                    continue

        avg_price = total_cost / total_qty if total_qty > 0 else 0
        
        # 현재가 조회 (캐싱)
        current_price = avg_price
        try:
            ticker = yf.Ticker(symbol)
            # 장중 데이터
            hist = ticker.history(period='1d')
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
        except:
            pass

        current_val = current_price * total_qty
        
        portfolio.append({
            "Symbol": symbol,
            "Name": name,
            "Strategy": strategy,
            "TargetAmount": target_amt,
            "PlanCount": plan_count,
            "Holdings": total_qty,
            "AvgPrice": avg_price,
            "CurrentPrice": current_price,
            "TotalInvested": total_cost,
            "CurrentValue": current_val,
            "ReturnRate": ((current_price - avg_price)/avg_price*100) if avg_price > 0 else 0,
            "BuyCount": buy_count
        })
        
    return pd.DataFrame(portfolio)

@st.cache_data(ttl=3600)
def get_stock_history_cached(symbol):
    try:
        return yf.Ticker(symbol).history(period="1y")
    except: return None

# =========================================================
# 메인 앱 실행
# =========================================================

df_stocks, df_trans, ss = load_data()
df_portfolio = calculate_portfolio(df_stocks, df_trans)

# 사이드바: 종목 추가 기능 (공통)
with st.sidebar:
    st.header("⚙️ 종목 마스터 관리")
    with st.expander("➕ 새 종목 등록하기"):
        with st.form("add_stock_sidebar"):
            new_sym = st.text_input("티커 (예: 005930.KS)")
            new_nm = st.text_input("종목명")
            new_str = st.selectbox("전략", ["Long", "Short"])
            new_tgt = st.number_input("최대 매수 가능액 (원)", min_value=0, step=100000)
            new_pln = st.number_input("분할 횟수", value=3)
            new_nte = st.text_input("메모")
            if st.form_submit_button("DB에 등록"):
                add_stock_to_db(new_sym, new_nm, new_str, new_tgt, new_pln, new_nte)
                st.success("등록 완료")
                st.rerun()

# 탭 구성
tab1, tab2 = st.tabs(["📈 주식 추적기 (Chart)", "💰 종목 관리 (Management)"])

# ---------------------------------------------------------
# 탭 1: 주식 추적기 (기존 기능 유지 + 새 DB 연동)
# ---------------------------------------------------------
with tab1:
    col_sel, col_dummy = st.columns([3, 1])
    with col_sel:
        if not df_portfolio.empty:
            # 검색용 리스트 생성
            search_list = [f"{row['Name']} ({row['Symbol']})" for _, row in df_portfolio.iterrows()]
            choice = st.selectbox("종목 선택", search_list)
            sym_tracker = choice.split("(")[1].replace(")", "")
            stock_info_t = df_portfolio[df_portfolio['Symbol'] == sym_tracker].iloc[0]
        else:
            st.info("등록된 종목이 없습니다.")
            sym_tracker = None

    if sym_tracker:
        st.subheader(f"{stock_info_t['Name']} 차트 분석")
        
        # 상단 지표
        m1, m2, m3 = st.columns(3)
        m1.metric("현재가", f"{stock_info_t['CurrentPrice']:,.0f}원")
        m2.metric("수익률", f"{stock_info_t['ReturnRate']:.2f}%")
        m3.metric("보유수량", f"{stock_info_t['Holdings']:,} 주")

        # 차트
        hist = get_stock_history_cached(sym_tracker)
        if hist is not None and not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=hist.index, open=hist['Open'], high=hist['High'],
                low=hist['Low'], close=hist['Close'], name='주가',
                increasing_line_color='#ef4444', decreasing_line_color='#3b82f6'
            ))
            
            # 매매 마커 표시
            if not df_trans.empty:
                my_txs = df_trans[df_trans['Symbol'] == sym_tracker]
                buys = my_txs[my_txs['Type'] == 'BUY']
                sells = my_txs[my_txs['Type'] == 'SELL']
                
                if not buys.empty:
                    fig.add_trace(go.Scatter(
                        x=pd.to_datetime(buys['Date']), y=buys['Price'], mode='markers',
                        marker=dict(symbol='triangle-up', size=12, color='red'), name='매수'
                    ))
                if not sells.empty:
                    fig.add_trace(go.Scatter(
                        x=pd.to_datetime(sells['Date']), y=sells['Price'], mode='markers',
                        marker=dict(symbol='triangle-down', size=12, color='blue'), name='매도'
                    ))
            
            fig.update_layout(height=500, xaxis_rangeslider_visible=False,
                              paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                              font=dict(color='white'))
            st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# 탭 2: 종목 관리 (요청하신 UI 구현)
# ---------------------------------------------------------
with tab2:
    st.title("💰 종목별 매수 현황 관리")
    
    # 상단 필터
    view_opt = st.radio("보기 필터", ["보유 종목", "관심 종목", "전체"], horizontal=True)
    
    target_df = df_portfolio.copy()
    if view_opt == "보유 종목": target_df = target_df[target_df['Holdings'] > 0]
    elif view_opt == "관심 종목": target_df = target_df[target_df['Holdings'] == 0]

    # 반복문으로 카드 생성
    for idx, row in target_df.iterrows():
        symbol = row['Symbol']
        name = row['Name']
        
        # --- [카드 UI 시작] ---
        with st.container():
            st.markdown(f"""
            <div class="stock-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                    <h3 style="margin:0;">{name} <span style="font-size:0.7em; color:#aaa;">({symbol})</span></h3>
                    <h3 style="margin:0; color:{'#ef4444' if row['ReturnRate'] > 0 else '#3b82f6'}">{row['ReturnRate']:.2f}%</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 1. 상단 정보 (TargetAmount, PlanCount 등)
            col_info1, col_info2, col_info3, col_info4 = st.columns(4)
            col_info1.metric("최대 매수 가능액", f"{row['TargetAmount']:,.0f}원")
            col_info2.metric("현재 총 매입금", f"{row['TotalInvested']:,.0f}원")
            col_info3.metric("매입 평단가", f"{row['AvgPrice']:,.0f}원")
            
            # 분할 횟수 수정 기능
            with col_info4:
                new_plan_cnt = st.number_input("분할 횟수 (수정가능)", value=int(row['PlanCount']), min_value=1, key=f"plan_{symbol}")
                if new_plan_cnt != row['PlanCount']:
                    if st.button("횟수 수정 저장", key=f"btn_plan_{symbol}"):
                        update_stock_plan_count(symbol, new_plan_cnt)
                        st.success("수정됨")
                        st.rerun()

            # 2. 진행률 바
            if row['TargetAmount'] > 0:
                progress_val = min(row['TotalInvested'] / row['TargetAmount'], 1.0)
                st.progress(progress_val)
                st.caption(f"매수 진행률: {progress_val*100:.1f}% (목표 {row['TargetAmount']:,.0f}원 중 {row['TotalInvested']:,.0f}원 소진)")
            else:
                st.progress(0)
                st.caption("목표 금액이 0원입니다.")

            st.markdown("---")

            # 3. 매수/매도/기록 탭
            action_t1, action_t2, action_t3 = st.tabs(["🔴 매수 기록 (계산기)", "🔵 매도 기록", "📝 최근 내역"])
            
            # [매수 탭] - 핵심 기능: 목표액/예상수량 계산
            with action_t1:
                # 계산 로직
                plan_cnt = int(row['PlanCount']) if row['PlanCount'] > 0 else 1
                target_per_round = row['TargetAmount'] / plan_cnt # 1회차 목표금액
                
                st.info(f"💡 1회차 목표 매수금액: **{target_per_round:,.0f}원** (총 {plan_cnt}회 중)")
                
                with st.form(key=f"buy_form_{symbol}"):
                    c1, c2, c3 = st.columns(3)
                    
                    with c1:
                        # 회차 자동 계산 (현재 매수 횟수 + 1)
                        next_round = row['BuyRounds'] + 1
                        st.text_input("회차 (자동)", value=f"{next_round}회차", disabled=True)
                    
                    with c2:
                        buy_date = st.date_input("매수일", datetime.now(), key=f"bd_{symbol}")
                    
                    with c3:
                        # 매수가 입력
                        buy_price = st.number_input("매수 단가 (원)", value=int(row['CurrentPrice']), step=100, key=f"bp_{symbol}")
                    
                    # 예상 수량 계산 및 표시
                    est_qty = math.floor(target_per_round / buy_price) if buy_price > 0 else 0
                    st.markdown(f"👉 목표 달성을 위한 예상 수량: **{est_qty:,} 주**")
                    
                    # 실제 입력
                    buy_qty = st.number_input("실제 매수 수량 (주)", value=est_qty, step=1, key=f"bq_{symbol}")
                    buy_note = st.text_input("메모", value=f"{next_round}회차 분할매수", key=f"bn_{symbol}")
                    
                    if st.form_submit_button("🔴 매수 기록 저장"):
                        add_transaction_to_db(buy_date, symbol, "BUY", buy_price, buy_qty, next_round, buy_note)
                        st.success("매수 기록 저장 완료!")
                        st.rerun()

            # [매도 탭]
            with action_t2:
                with st.form(key=f"sell_form_{symbol}"):
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        sell_date = st.date_input("매도일", datetime.now(), key=f"sd_{symbol}")
                        sell_price = st.number_input("매도 단가", value=int(row['CurrentPrice']), step=100, key=f"sp_{symbol}")
                    with sc2:
                        sell_qty = st.number_input("매도 수량", min_value=1, max_value=int(row['Holdings']), step=1, key=f"sq_{symbol}")
                        sell_note = st.text_input("메모", key=f"sn_{symbol}")
                    
                    # 예상 수익금 표시
                    est_profit = (sell_price - row['AvgPrice']) * sell_qty
                    est_yield = ((sell_price - row['AvgPrice']) / row['AvgPrice'] * 100) if row['AvgPrice'] > 0 else 0
                    
                    st.caption(f"예상 실현손익: {est_profit:,.0f}원 ({est_yield:.2f}%)")
                    
                    if st.form_submit_button("🔵 매도 기록 저장"):
                        add_transaction_to_db(sell_date, symbol, "SELL", sell_price, sell_qty, 0, sell_note)
                        st.success("매도 기록 저장 완료!")
                        st.rerun()

            # [기록 탭]
            with action_t3:
                if not df_trans.empty:
                    my_txs = df_trans[df_trans['Symbol'] == symbol].sort_values(by='Date', ascending=False).head(5)
                    if not my_txs.empty:
                        st.dataframe(my_txs[['Date', 'Type', 'Price', 'Quantity', 'Note']], hide_index=True, use_container_width=True)
                    else:
                        st.caption("아직 거래 내역이 없습니다.")
            
            st.write("") # 간격 띄우기
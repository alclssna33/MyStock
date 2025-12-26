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

# ★★★ [CSS 수정] 드롭다운 글시 안보임 해결 + 카드 스타일 ★★★
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700&display=swap');
    
    /* 전체 배경 (다크) */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        font-family: 'Pretendard', sans-serif;
        color: #FFFFFF !important;
    }
    
    /* 사이드바 배경 */
    [data-testid="stSidebar"] {
        background-color: #1a1a2e !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* 기본 텍스트 화이트 */
    h1, h2, h3, h4, h5, h6, p, label, span { color: #FFFFFF !important; }
    
    /* [수정] SelectBox 및 Input 내부 텍스트 문제 해결 */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    div[data-baseweb="popover"] div, div[data-baseweb="menu"] div {
        color: #000000 !important; /* 드롭다운 메뉴 글씨 검정 */
    }
    input[type="text"], input[type="number"], input[type="date"] {
        color: #000000 !important;
        background-color: #ffffff !important;
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
        color: #aaaaaa !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #6366f1 !important;
        color: white !important;
        font-weight: bold;
    }
    
    /* 카드 컨테이너 스타일 */
    .stock-card {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* 진행률 바 커스텀 */
    .stProgress > div > div > div > div {
        background-color: #6366f1;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 구글 시트 연결 설정 ---
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
            st.error("❌ secrets.json 없음")
            st.stop()
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ 인증 오류: {e}")
        st.stop()

def init_google_sheet():
    client = get_google_sheets_client()
    try:
        return client.open(SPREADSHEET_NAME)
    except Exception as e:
        st.error(f"❌ 시트 연결 실패: {e}")
        st.stop()

# --- 3. 데이터 로드/저장 ---

def load_data():
    spreadsheet = init_google_sheet()
    try:
        ws_stocks = spreadsheet.worksheet("Stocks")
        df_stocks = pd.DataFrame(ws_stocks.get_all_records())
        if df_stocks.empty and 'Symbol' not in df_stocks.columns:
             df_stocks = pd.DataFrame(columns=["Symbol", "Name", "Category", "Strategy", "TargetAmount", "PlanCount", "InterestDate", "Note"])
    except:
        df_stocks = pd.DataFrame(columns=["Symbol", "Name", "Category", "Strategy", "TargetAmount", "PlanCount", "InterestDate", "Note"])

    try:
        ws_trans = spreadsheet.worksheet("Transactions")
        df_trans = pd.DataFrame(ws_trans.get_all_records())
        if df_trans.empty and 'Symbol' not in df_trans.columns:
            df_trans = pd.DataFrame(columns=["Date", "Symbol", "Type", "Price", "Quantity", "Round", "Note"])
    except:
         df_trans = pd.DataFrame(columns=["Date", "Symbol", "Type", "Price", "Quantity", "Round", "Note"])
    
    return df_stocks, df_trans

def add_stock_to_db(symbol, name, strategy, target_amt, plan_count, note):
    client = get_google_sheets_client()
    ws = client.open(SPREADSHEET_NAME).worksheet("Stocks")
    ws.append_row([symbol.upper(), name, "Interest", strategy, target_amt, plan_count, str(datetime.now().date()), note])
    st.cache_data.clear()

def add_transaction_to_db(date, symbol, t_type, price, qty, round_num, note):
    client = get_google_sheets_client()
    ss = client.open(SPREADSHEET_NAME)
    ws_trans = ss.worksheet("Transactions")
    ws_trans.append_row([str(date), symbol.upper(), t_type, price, qty, round_num, note])
    
    if t_type == "BUY":
        try:
            ws_stocks = ss.worksheet("Stocks")
            stocks_data = ws_stocks.get_all_records()
            df_stocks = pd.DataFrame(stocks_data)
            mask = df_stocks['Symbol'] == symbol.upper()
            if mask.any():
                row_idx = df_stocks.index[mask][0] + 2
                ws_stocks.update_cell(row_idx, 3, "Holding") 
        except:
            pass
    st.cache_data.clear()

# --- 4. 계산 로직 ---
def calculate_portfolio(df_stocks, df_trans):
    portfolio = []
    if df_stocks.empty: return pd.DataFrame()

    for _, stock in df_stocks.iterrows():
        symbol = str(stock['Symbol']).strip()
        name = stock['Name']
        strategy = stock.get('Strategy', 'Long')
        category = stock.get('Category', 'Interest')
        
        # 목표금액 & 분할횟수 처리
        try: target_amt = float(str(stock.get('TargetAmount', 0)).replace(',',''))
        except: target_amt = 0
        try: plan_count = int(str(stock.get('PlanCount', 3)).replace(',',''))
        except: plan_count = 3

        if not df_trans.empty:
            txs = df_trans[df_trans['Symbol'].astype(str) == symbol]
        else:
            txs = pd.DataFrame()

        total_qty = 0
        total_cost = 0
        realized_profit = 0
        buy_rounds = 0 # 매수 진행 회차
        
        if not txs.empty:
            for _, tx in txs.iterrows():
                try:
                    qty = int(str(tx['Quantity']).replace(',',''))
                    price = float(str(tx['Price']).replace(',',''))
                    t_type = tx['Type']
                    
                    if t_type == 'BUY':
                        total_cost += price * qty
                        total_qty += qty
                        buy_rounds += 1 # 매수 횟수 카운트
                    elif t_type == 'SELL':
                        if total_qty > 0:
                            avg_price = total_cost / total_qty
                            profit = (price - avg_price) * qty
                            realized_profit += profit
                            total_cost -= avg_price * qty
                            total_qty -= qty
                except:
                    continue

        avg_price = total_cost / total_qty if total_qty > 0 else 0
        current_price = avg_price
        
        # 현재가 조회 (캐싱)
        try:
            ticker = yf.Ticker(symbol)
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
            "TargetAmount": target_amt,
            "PlanCount": plan_count,
            "BuyRounds": buy_rounds
        })

    return pd.DataFrame(portfolio)

@st.cache_data(ttl=3600)
def get_stock_history(symbol):
    try:
        return yf.Ticker(symbol).history(period="1y")
    except: return None

# --- 메인 앱 시작 ---
df_stocks, df_trans = load_data()
df_portfolio = calculate_portfolio(df_stocks, df_trans)

with st.sidebar:
    st.header("⚙️ 종목 관리")
    with st.expander("➕ 새 종목 등록 (Stocks)", expanded=False):
        with st.form("add_stock_form"):
            new_symbol = st.text_input("티커 (예: 005930.KS)")
            new_name = st.text_input("종목명")
            new_strategy = st.selectbox("전략", ["Long", "Short"])
            new_target = st.number_input("목표 투자금 (원)", min_value=0, step=100000)
            new_plan = st.number_input("분할 계획 (회)", value=3)
            new_note = st.text_input("메모")
            if st.form_submit_button("등록"):
                if new_symbol and new_name:
                    add_stock_to_db(new_symbol, new_name, new_strategy, new_target, new_plan, new_note)
                    st.success(f"{new_name} 등록 완료!")
                    st.rerun()

tab_tracker, tab_manager = st.tabs(["📈 주식 추적기", "💰 주식 관리 (포트폴리오)"])

# ----------------------------------------------------
# 탭 1: 추적기 (기존 기능 유지)
# ----------------------------------------------------
with tab_tracker:
    col1, col2 = st.columns([3, 1])
    with col1:
        if not df_portfolio.empty:
            options = [f"{row['Name']} ({row['Symbol']})" for _, row in df_portfolio.iterrows()]
            selected_option = st.selectbox("종목 선택", options, key="tracker_select")
            selected_symbol = selected_option.split("(")[1].replace(")", "")
            selected_stock_info = df_portfolio[df_portfolio['Symbol'] == selected_symbol].iloc[0]
        else:
            st.warning("종목이 없습니다.")
            selected_symbol = None

    if selected_symbol:
        st.subheader(f"{selected_stock_info['Name']} 차트")
        # 메트릭
        m1, m2, m3 = st.columns(3)
        m1.metric("현재가", f"{selected_stock_info['CurrentPrice']:,.0f}원")
        m2.metric("보유수량", f"{selected_stock_info['Holdings']:,} 주")
        m3.metric("평가손익", f"{selected_stock_info['UnrealizedProfit']:,.0f}원", f"{selected_stock_info['ReturnRate']:.2f}%")
        
        # 차트
        hist_df = get_stock_history(selected_symbol)
        if hist_df is not None:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=hist_df.index, open=hist_df['Open'], high=hist_df['High'], low=hist_df['Low'], close=hist_df['Close'], name='주가', increasing_line_color='#ef4444', decreasing_line_color='#3b82f6'))
            # 마커 표시 로직
            if not df_trans.empty:
                txs = df_trans[df_trans['Symbol'] == selected_symbol]
                buys = txs[txs['Type'] == 'BUY']
                sells = txs[txs['Type'] == 'SELL']
                if not buys.empty: fig.add_trace(go.Scatter(x=pd.to_datetime(buys['Date']), y=buys['Price'], mode='markers', marker=dict(symbol='triangle-up', size=12, color='red'), name='매수'))
                if not sells.empty: fig.add_trace(go.Scatter(x=pd.to_datetime(sells['Date']), y=sells['Price'], mode='markers', marker=dict(symbol='triangle-down', size=12, color='blue'), name='매도'))
            
            fig.update_layout(height=500, xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
            st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# 탭 2: 주식 관리 (카드형 UI + 분할매수 계산기)
# ----------------------------------------------------
with tab_manager:
    st.title("💰 내 보유 주식 관리")
    
    # 상단 요약
    if not df_portfolio.empty:
        total_iv = df_portfolio['TotalInvested'].sum()
        total_val = df_portfolio['CurrentValue'].sum()
        total_pl = total_val - total_iv
        
        c1, c2, c3 = st.columns(3)
        c1.metric("총 매입금", f"{total_iv:,.0f}원")
        c2.metric("총 평가금", f"{total_val:,.0f}원")
        c3.metric("총 평가손익", f"{total_pl:,.0f}원", f"{(total_pl/total_iv*100 if total_iv>0 else 0):.2f}%")
        st.divider()

    # 필터
    col_f1, col_f2 = st.columns([1, 4])
    with col_f1:
        view_filter = st.radio("보기 옵션", ["보유 종목", "관심 종목", "전체"], index=0)

    # 필터링 로직
    target_df = df_portfolio.copy()
    if view_filter == "보유 종목":
        target_df = target_df[target_df['Holdings'] > 0]
    elif view_filter == "관심 종목":
        target_df = target_df[target_df['Holdings'] == 0]

    # ★★★ [카드형 UI 반복문] ★★★
    for idx, row in target_df.iterrows():
        symbol = row['Symbol']
        
        # 카드 컨테이너 시작
        with st.container():
            st.markdown(f"""
            <div class="stock-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3>{row['Name']} <span style="font-size:0.8em; color:#aaaaaa;">({symbol})</span></h3>
                    <h3 style="color: {'#ef4444' if row['ReturnRate'] > 0 else '#3b82f6'};">{row['ReturnRate']:.2f}%</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col_left, col_right = st.columns([1, 1.5])
            
            # [왼쪽] 기본 정보 및 진행률
            with col_left:
                st.write(f"**현재가:** {row['CurrentPrice']:,.0f}원")
                st.write(f"**평단가:** {row['AvgPrice']:,.0f}원")
                st.write(f"**보유수량:** {row['Holdings']:,}주")
                st.write(f"**총 매입:** {row['TotalInvested']:,.0f}원")
                
                # 진행률 바 (총 매입 / 목표 금액)
                target_amt = row['TargetAmount']
                if target_amt > 0:
                    progress = min(row['TotalInvested'] / target_amt, 1.0)
                    st.progress(progress)
                    st.caption(f"목표 {target_amt:,.0f}원 중 {progress*100:.1f}% 달성")
                else:
                    st.caption("목표 금액 미설정")

            # [오른쪽] 매수/매도/기록 탭 (계산기 기능 포함)
            with col_right:
                action_tab1, action_tab2, action_tab3 = st.tabs(["🔴 분할 매수", "🔵 매도", "📝 기록"])
                
                # 1. 분할 매수 계산기 탭
                with action_tab1:
                    # 목표액 기반 계산
                    plan_count = row['PlanCount'] if row['PlanCount'] > 0 else 1
                    target_amt = row['TargetAmount']
                    amount_per_round = target_amt / plan_count if plan_count > 0 else 0
                    
                    st.info(f"🎯 1회차 목표 매수금액: **{amount_per_round:,.0f}원** (총 {plan_count}회 분할)")
                    
                    with st.form(key=f"buy_form_{symbol}"):
                        c_p, c_q = st.columns(2)
                        with c_p:
                            # 매수가 입력
                            buy_price = st.number_input("매수 단가 (원)", value=int(row['CurrentPrice']), step=100, key=f"bp_{symbol}")
                        
                        # 예상 수량 자동 계산 표시
                        est_qty = int(amount_per_round // buy_price) if buy_price > 0 else 0
                        st.markdown(f"👉 예상 매수 수량: **{est_qty:,} 주**")
                        
                        with c_q:
                            # 실제 매수량 입력 (예상값 참고해서 입력)
                            buy_qty = st.number_input("실제 매수량 (주)", value=est_qty, step=1, key=f"bq_{symbol}")
                            
                        buy_date = st.date_input("매수일", datetime.now(), key=f"bd_{symbol}")
                        buy_note = st.text_input("메모 (예: 1회차)", value=f"{row['BuyRounds']+1}회차", key=f"bn_{symbol}")
                        
                        if st.form_submit_button("🔴 매수 기록 저장"):
                            # 다음 회차 자동 계산
                            next_round = row['BuyRounds'] + 1
                            add_transaction_to_db(buy_date, symbol, "BUY", buy_price, buy_qty, next_round, buy_note)
                            st.success("저장되었습니다!")
                            st.rerun()

                # 2. 매도 탭
                with action_tab2:
                    with st.form(key=f"sell_form_{symbol}"):
                        s_p, s_q = st.columns(2)
                        with s_p: sell_price = st.number_input("매도 단가", value=int(row['CurrentPrice']), step=100, key=f"sp_{symbol}")
                        with s_q: sell_qty = st.number_input("매도 수량", min_value=1, max_value=int(row['Holdings']), step=1, key=f"sq_{symbol}")
                        sell_date = st.date_input("매도일", datetime.now(), key=f"sd_{symbol}")
                        sell_note = st.text_input("메모", key=f"sn_{symbol}")
                        
                        if st.form_submit_button("🔵 매도 기록 저장"):
                            add_transaction_to_db(sell_date, symbol, "SELL", sell_price, sell_qty, 0, sell_note)
                            st.success("매도 완료!")
                            st.rerun()

                # 3. 기록 탭
                with action_tab3:
                    if not df_trans.empty:
                        my_txs = df_trans[df_trans['Symbol'] == symbol].sort_values(by='Date', ascending=False).head(5)
                        if not my_txs.empty:
                            st.dataframe(my_txs[['Date', 'Type', 'Price', 'Quantity', 'Note']], hide_index=True)
                        else:
                            st.caption("거래 내역 없음")
            
            st.markdown("---") # 카드 구분선
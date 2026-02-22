import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import re
from datetime import datetime, timedelta

# 모듈화된 커스텀 라이브러리 임포트
from ui_styles import inject_custom_css
from database import (
    init_google_sheet, load_stocks, save_stocks, 
    load_split_purchase_data, save_split_purchase_data
)
from stock_utils import (
    get_stock_data, get_daily_change, check_week80_condition, get_week80_gap,
    parse_date_safe, find_trading_date
)
from ui_components import create_overlay_badge, portfolio_summary_card

# 페이지 설정
st.set_page_config(
    page_title="나만의 주식 추적기",
    page_icon="📈",
    layout="wide"
)

# UI 스타일 주입
inject_custom_css()

# Google Sheets 초기화
init_google_sheet()

# 관심종목 주80 이격도 일괄 업데이트 함수
def update_week80_gaps():
    """모든 관심종목의 주80 이격도를 계산해 Google Sheets Week80Gap 컬럼에 저장합니다."""
    try:
        df = load_stocks()
        if df.empty:
            return

        if 'Week80Gap' not in df.columns:
            df['Week80Gap'] = ""

        updated = False
        for idx, row in df.iterrows():
            # 관심종목만 처리 (BuyTransactions 없고 InterestDate 있는 종목)
            buy_txs_str = row.get('BuyTransactions', '[]')
            has_buy = False
            try:
                if pd.notna(buy_txs_str) and str(buy_txs_str).strip():
                    buy_txs = json.loads(buy_txs_str) if isinstance(buy_txs_str, str) else buy_txs_str
                    if buy_txs and len(buy_txs) > 0:
                        has_buy = True
            except Exception:
                pass

            if not has_buy and pd.notna(row.get('InterestDate', '')) and str(row.get('InterestDate', '')).strip() != "":
                symbol = row.get('Symbol', '')
                if symbol and pd.notna(symbol):
                    gap = get_week80_gap(str(symbol).strip())
                    if gap is not None:
                        df.at[idx, 'Week80Gap'] = str(gap)
                        updated = True

        if updated:
            save_stocks(df)
    except Exception:
        pass  # 업데이트 실패 시 앱 동작 중단 없이 계속 진행

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

        # Symbol 정규화: 대소문자 무시, 공백 제거, 숫자만인 경우 6자리 0패딩
        symbol_normalized = symbol.strip().upper()
        if symbol_normalized.isdigit():
            symbol_normalized = symbol_normalized.zfill(6)
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
                "SellTransactions": "[]",
                "Week80Gap": ""
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
            # 형식: "Name (Symbol)" 에서 Symbol 추출
            selected_symbol = selected_delete.split("(")[-1].rstrip(")").strip()
            # 타입 안전 비교 (Symbol이 int로 읽혔을 경우 대비)
            mask = df['Symbol'].astype(str).str.strip() == selected_symbol
            deleted_name = df.loc[mask, 'Name'].values[0] if mask.any() else selected_delete.split("(")[0].strip()
            if mask.any():
                df = df[~mask].reset_index(drop=True)
                save_stocks(df)
                st.success(f"{deleted_name} 종목이 삭제되었습니다!")
                st.rerun()
            else:
                st.error(f"'{selected_symbol}' 종목을 찾을 수 없습니다.")
    else:
        st.info("저장된 종목이 없습니다.")

# 종목 상세 정보를 보여주는 Modal 함수
@st.dialog("📊 종목 상세 관리")
def show_stock_detail_modal(stock_id):
    """종목 상세 정보를 Modal Popup으로 표시"""
    # 최신 데이터 로드
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
    installments = int(stock_row.get('Installments', 3))
    
    # Transactions 파싱
    def parse_txs(raw):
        if pd.isna(raw) or not str(raw).strip(): return []
        if isinstance(raw, list): return raw
        try: return json.loads(raw)
        except: return []

    buy_txs = parse_txs(stock_row.get('BuyTransactions', '[]'))
    sell_txs = parse_txs(stock_row.get('SellTransactions', '[]'))
    
    try: market_cap_value = float(market_cap) if pd.notna(market_cap) else 0
    except: market_cap_value = 0
    
    max_investment = market_cap_value / 10000
    
    # === 이동평균법 계산 ===
    all_transactions = []
    for tx in buy_txs:
        if isinstance(tx, dict) and tx.get('date') and tx.get('price') and tx.get('quantity'):
            try: all_transactions.append({'type': 'buy', 'date': pd.to_datetime(tx['date']).date(), 'price': float(tx['price']), 'quantity': int(tx['quantity']), 'original_tx': tx})
            except: pass
    for tx in sell_txs:
        if isinstance(tx, dict) and tx.get('date') and tx.get('price') and tx.get('quantity'):
            try: all_transactions.append({'type': 'sell', 'date': pd.to_datetime(tx['date']).date(), 'price': float(tx['price']), 'quantity': int(tx['quantity']), 'original_tx': tx})
            except: pass
    
    all_transactions.sort(key=lambda x: (x['date'], 0 if x['type'] == 'buy' else 1))
    
    current_qty, current_avg_price, total_realized_profit = 0, 0.0, 0.0
    for tx in all_transactions:
        if tx['type'] == 'buy':
            if current_qty == 0:
                current_avg_price, current_qty = tx['price'], tx['quantity']
            else:
                total_cost = (current_qty * current_avg_price) + (tx['quantity'] * tx['price'])
                current_qty += tx['quantity']
                current_avg_price = total_cost / current_qty
        elif tx['type'] == 'sell':
            if current_avg_price > 0:
                profit = (tx['price'] - current_avg_price) * tx['quantity']
                tx['original_tx']['realized_profit'] = profit
                tx['original_tx']['yield_pct'] = (tx['price'] - current_avg_price) / current_avg_price * 100
                total_realized_profit += profit
            current_qty = max(0, current_qty - tx['quantity'])
    
    current_invested = current_qty * current_avg_price
    progress = (current_invested / max_investment * 100) if max_investment > 0 else 0
    
    st.subheader(f"{stock_name}")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("최대 매수 가능액", f"{max_investment:,.0f}원")
    col2.metric("총 매입금액", f"{current_invested:,.0f}원")
    col3.metric("매입 평단가", f"{current_avg_price:,.0f}원")
    col4.metric("보유 수량", f"{current_qty:,} 주")
    
    with col5:
        st.write("**분할 횟수**")
        new_installments = st.number_input("수정", min_value=1, value=installments, step=1, key=f"edit_inst_{stock_id}", label_visibility="collapsed")
        if new_installments != installments:
            if st.button("적용", key=f"apply_inst_{stock_id}", use_container_width=True):
                df_split.at[stock_idx, 'Installments'] = int(new_installments)
                save_split_purchase_data(df_split)
                st.success("수정되었습니다!")
                st.rerun(scope="app")
    
    st.progress(max(0.0, min(1.0, progress / 100)))
    col_p1, col_p2 = st.columns(2)
    col_p1.write(f"**매수 진행률: {progress:.2f}%**")
    col_p2.write(f"**총 실현손익: {total_realized_profit:,.0f}원**")
    
    st.divider()
    col_buy, col_sell = st.columns(2)
    
    with col_buy:
        st.subheader("매수 계획 및 기록")
        for i in range(installments):
            tx = buy_txs[i] if i < len(buy_txs) else None
            with st.form(f"buy_form_{stock_id}_{i}"):
                c1, c2, c3, c4 = st.columns([1, 1.5, 1, 1])
                b_date = c1.date_input("날짜", value=pd.to_datetime(tx['date']).date() if tx and tx.get('date') else datetime.now().date(), key=f"bd_{stock_id}_{i}")
                b_price = c2.number_input("매수가", min_value=0, value=int(tx['price']) if tx and tx.get('price') else 0, key=f"bp_{stock_id}_{i}")
                b_qty = c3.number_input("수량", min_value=0, value=int(tx['quantity']) if tx and tx.get('quantity') else 0, key=f"bq_{stock_id}_{i}")
                if c4.form_submit_button("저장", type="primary"):
                    if b_price > 0 and b_qty > 0:
                        while len(buy_txs) <= i: buy_txs.append(None)
                        buy_txs[i] = {'date': str(b_date), 'price': int(b_price), 'quantity': int(b_qty)}
                        df_split.at[stock_idx, 'BuyTransactions'] = json.dumps([t for t in buy_txs if t])
                        save_split_purchase_data(df_split)
                        st.success("저장되었습니다!")
                        st.rerun(scope="app")
    
    with col_sell:
        st.subheader("분할 매도 기록")
        with st.form(f"sell_form_{stock_id}"):
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            s_date = c1.date_input("날짜", value=datetime.now().date(), key=f"sd_{stock_id}")
            s_price = c2.number_input("매도가", min_value=0, key=f"sp_{stock_id}")
            s_qty = c3.number_input("수량", min_value=1, key=f"sq_{stock_id}")
            if c4.form_submit_button("추가", type="primary"):
                sell_txs.append({'id': str(datetime.now().timestamp()), 'date': str(s_date), 'price': float(s_price), 'quantity': int(s_qty)})
                df_split.at[stock_idx, 'SellTransactions'] = json.dumps(sell_txs)
                save_split_purchase_data(df_split)
                st.success("저장되었습니다!")
                st.rerun(scope="app")
        
        for i, tx in enumerate(sell_txs):
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 1, 1, 0.5])
                c1.write(f"{tx['date']} | {tx['price']:,.0f}원 | {tx['quantity']}주")
                if c4.button("🗑️", key=f"del_s_{stock_id}_{i}"):
                    sell_txs.pop(i)
                    df_split.at[stock_idx, 'SellTransactions'] = json.dumps(sell_txs)
                    save_split_purchase_data(df_split)
                    st.rerun(scope="app")

    st.divider()
    col_exit, col_del = st.columns(2)

    with col_exit:
        if st.button("📤 매도 종료 (관심종목 전환)", key=f"exit_stock_{stock_id}", use_container_width=True):
            df_all = load_stocks()
            sym_mask = df_all['Symbol'].astype(str).str.strip() == str(stock_id).strip()
            if sym_mask.any():
                idx = df_all[sym_mask].index[0]
                # 플래너에서 제외: Installments·Category 초기화
                df_all.at[idx, 'Installments'] = ""
                df_all.at[idx, 'Category'] = ""
                # 관심종목 조건 충족: 거래 기록 초기화 + 관심일 갱신
                df_all.at[idx, 'BuyTransactions'] = "[]"
                df_all.at[idx, 'SellTransactions'] = "[]"
                df_all.at[idx, 'InterestDate'] = datetime.now().strftime("%Y-%m-%d")
                save_stocks(df_all)
            st.rerun(scope="app")

    with col_del:
        if st.button(f"🗑️ {stock_name} 삭제", key=f"del_stock_{stock_id}", type="secondary", use_container_width=True):
            df_all = load_stocks()
            mask = df_all['Symbol'].astype(str).str.strip() != str(stock_id).strip()
            df_all = df_all[mask].reset_index(drop=True)
            save_stocks(df_all)
            st.rerun(scope="app")

# === Fragment 렌더링 함수 정의 ===
# 탭별 Fragment로 분리하여 탭 간 상호 재실행 방지

@st.fragment
def render_tracker_tab():
    """탭1: 주식 추적기 - 독립 실행 Fragment"""
    st.title("📈 나만의 주식 추적기")
    
    df = load_stocks()

    if df.empty:
        st.info("사이드바에서 종목을 추가해주세요.")
    else:
        # 상단 컨트롤 바 (대시보드 헤더 스타일)
        st.markdown('<div class="dashboard-header">', unsafe_allow_html=True)
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
            elif category == "관심종목":
                # 관심종목 선택 시 정렬/필터 옵션 표시
                st.write("옵션")
                col_opt1, col_opt2, col_opt3 = st.columns([1, 1, 1.2])
                with col_opt1:
                    prev_sort_state = st.session_state.get("sort_by_change", False)
                    sort_by_change = st.checkbox("상승률순", key="sort_by_change", value=False)
                with col_opt2:
                    prev_week80_state = st.session_state.get("week80_check", False)
                    week80_check = st.checkbox("주80", key="week80_check", value=False)
                with col_opt3:
                    if week80_check:
                        if st.button("🔄", key="week80_update_btn", help="주80 이격도 업데이트"):
                            with st.spinner("업데이트 중..."):
                                update_week80_gaps()
                            load_stocks.clear()
                            st.rerun(scope="fragment")
                
                # 체크박스 상태가 변경되면 캐시 초기화
                if prev_sort_state != sort_by_change or prev_week80_state != week80_check:
                    # 관련 캐시 키들 제거
                    keys_to_remove = [k for k in st.session_state.keys() if k.startswith("interest_stocks_change_")]
                    for key in keys_to_remove:
                        if key in st.session_state:
                            del st.session_state[key]
                    if 'interest_stocks_cache_symbols' in st.session_state:
                        del st.session_state['interest_stocks_cache_symbols']
                
                strategy = "전체"
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
                
                # 주80 체크 여부 확인
                is_week80 = st.session_state.get("week80_check", False)
                
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
                        # 주80 필터 적용 (저장된 Week80Gap 사용 → 빠른 응답)
                        if is_week80:
                            week80_gap_val = row.get('Week80Gap', None)
                            if week80_gap_val is None or pd.isna(week80_gap_val) or str(week80_gap_val).strip() == '':
                                continue  # 미계산 종목 제외
                            try:
                                if abs(float(str(week80_gap_val).strip())) > 10:
                                    continue  # 이격도 10% 초과 제외
                            except (ValueError, TypeError):
                                continue

                        stock_display = f"{row['Name']} ({row['Symbol']})"
                        filtered_options.append(stock_display)
                        # ChangeRate 및 Week80Gap 컬럼에서 값 가져오기
                        change_rate = row.get('ChangeRate', None)
                        week80_gap_stored = row.get('Week80Gap', None)
                        interest_stocks_data.append({
                            'display': stock_display,
                            'symbol': row['Symbol'],
                            'name': row['Name'],
                            'change_rate': change_rate,  # Google Sheets의 J열 값
                            'week80_gap': week80_gap_stored  # Google Sheets의 K열 값
                        })
                if filtered_options:
                    stock_options = filtered_options
                    
                    # 상승률순 체크박스는 이제 col2에서 처리됨
                    sort_by_change = st.session_state.get("sort_by_change", False)
                    
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
                    elif is_week80 and interest_stocks_data:
                        # 주80 이격도 기준 정렬 (절대값 오름차순 - MA80에 가장 가까운 순)
                        week80_sort = []
                        for stock_info in interest_stocks_data:
                            raw_gap = stock_info.get('week80_gap', None)
                            abs_gap = float('inf')
                            if raw_gap is not None and pd.notna(raw_gap) and str(raw_gap).strip() != '':
                                try:
                                    abs_gap = abs(float(str(raw_gap).strip()))
                                except (ValueError, TypeError):
                                    pass
                            week80_sort.append({'info': stock_info, 'abs_gap': abs_gap})
                        week80_sort.sort(key=lambda x: x['abs_gap'])
                        stock_options = []
                        for item in week80_sort:
                            si = item['info']
                            raw_gap = si.get('week80_gap', None)
                            if raw_gap is not None and pd.notna(raw_gap) and str(raw_gap).strip() != '':
                                try:
                                    gap_pct = float(str(raw_gap).strip())
                                    stock_options.append(f"{si.get('name', '')} ({si.get('symbol', '')}) {gap_pct:+.1f}%")
                                except (ValueError, TypeError):
                                    stock_options.append(si.get('display', ''))
                            else:
                                stock_options.append(si.get('display', ''))
                    else:
                        # 가나다순 정렬 (기본값)
                        stock_options = sorted(stock_options)

            # 가나다순 정렬 (상승률순/주80순이 아닐 때만)
            if category != "관심종목" or (not st.session_state.get("sort_by_change", False) and not st.session_state.get("week80_check", False)):
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
            
            selected_stock = st.selectbox(
                "종목 검색/선택",
                stock_options,
                key="stock_select",
                placeholder="종목명 또는 코드 입력..."
            )
            
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
        st.markdown('</div>', unsafe_allow_html=True)
        
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
                    
                    # --- 캔들스틱 차트 ---
                    st.markdown('<div class="content-card">', unsafe_allow_html=True)

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
                            line=dict(color='#FF4444', width=1),  # 상승: 빨강
                            fillcolor='#FF4444'
                        ),
                        decreasing=dict(
                            line=dict(color='#4499FF', width=1),  # 하락: 파랑
                            fillcolor='#4499FF'
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
                            ma_20_daily = ma_20.reindex(stock_data.index, method='ffill')
                            fig.add_trace(go.Scatter(
                                x=stock_data.index,
                                y=ma_20_daily,
                                mode='lines',
                                name='20주 MA',
                                line=dict(color='#FFB347', width=1.8),  # 밝은 주황
                                hovertemplate='20주 MA: %{y:,.0f}<extra></extra>'
                            ))

                        # 80주 이동평균 계산
                        if len(weekly_data) >= 80:
                            ma_80 = weekly_data['Close'].rolling(window=80).mean()
                            ma_80_daily = ma_80.reindex(stock_data.index, method='ffill')
                            fig.add_trace(go.Scatter(
                                x=stock_data.index,
                                y=ma_80_daily,
                                mode='lines',
                                name='80주 MA',
                                line=dict(color='#00E5A0', width=2),  # 밝은 민트
                                hovertemplate='80주 MA: %{y:,.0f}<extra></extra>'
                            ))
                    except Exception as e:
                        # 이동평균 계산 실패 시 무시 (차트는 정상 표시)
                        pass

                    
                    # 날짜별 주석 추가
                    annotations = []
                    sell_dates = []
                    sell_prices = []
                    
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
                            tickfont=dict(color='#b0b8c8', size=11),
                            gridcolor='rgba(90, 100, 130, 0.35)',
                            gridwidth=1,
                            showgrid=True,
                            zeroline=False,
                            linecolor='rgba(255, 255, 255, 0.15)',
                            linewidth=1
                        ),
                        yaxis=dict(
                            tickfont=dict(color='#b0b8c8', size=11),
                            gridcolor='rgba(90, 100, 130, 0.35)',
                            gridwidth=1,
                            showgrid=True,
                            zeroline=False,
                            linecolor='rgba(255, 255, 255, 0.15)',
                            linewidth=1,
                            tickformat=',d'
                        ),
                        xaxis_rangeslider_visible=False,
                        height=620,
                        annotations=annotations,
                        hovermode=False,
                        dragmode=False,
                        plot_bgcolor='rgba(18, 20, 30, 1)',
                        paper_bgcolor='rgba(24, 26, 38, 1)',
                        font=dict(family='Pretendard', color='#e5e7eb'),
                        margin=dict(l=60, r=20, t=60, b=40),
                        legend=dict(
                            bgcolor='rgba(30, 33, 50, 0.85)',
                            bordercolor='rgba(120, 130, 180, 0.3)',
                            borderwidth=1,
                            font=dict(color='#e0e6ff', size=12),
                            orientation='h',
                            yanchor='bottom',
                            y=1.01,
                            xanchor='left',
                            x=0
                        )
                    )
                    
                    # 차트 표시 (마우스 인터랙션 비활성화)
                    st.plotly_chart(fig, use_container_width=True, config={
                        'staticPlot': True,
                        'displayModeBar': False,
                        'displaylogo': False,
                        'scrollZoom': False,
                        'toImageButtonOptions': {
                            'format': 'png',
                            'filename': f'{name}_{symbol}_chart',
                            'height': 620,
                            'width': 1200,
                            'scale': 1
                        }
                    })
                    
                    # 메모 표시
                    if pd.notna(note) and note != "":
                        st.markdown(f"**메모:** {note}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.error(f"{symbol} 종목의 데이터를 가져올 수 없습니다. 티커를 확인해주세요.")


def render_planner_tab():
    """탭2: 분할 매수 플래너

    NOTE: @st.fragment 미적용 - Streamlit 제약으로 Fragment 내부에서
    @st.dialog 함수(show_stock_detail_modal)를 콜백으로 호출 불가.
    render_tracker_tab만 Fragment로 유지.
    """
    st.title("💰 주식 분할 매수 플래너")
    
    df_all = load_stocks()
    # Installments가 있는 종목만 필터링
    df_split = df_all[df_all['Installments'].apply(lambda x: pd.notna(x) and str(x).strip() != "" and str(x) != "0")].copy()
    
    if df_split.empty:
        st.info("추가된 종목이 없습니다. 우측 상단에서 종목을 추가하거나 관심종목에서 가져오세요.")
    else:
        # 포트폴리오 데이터 계산
        portfolio_list = []
        total_invested, total_budget = 0, 0
        
        for _, stock in df_split.iterrows():
            def parse_json(x):
                try: return json.loads(x) if isinstance(x, str) else (x if isinstance(x, list) else [])
                except: return []
            
            buys = parse_json(stock.get('BuyTransactions', '[]'))
            sells = parse_json(stock.get('SellTransactions', '[]'))
            
            buy_cost = sum(float(t.get('price', 0)) * int(t.get('quantity', 0)) for t in buys if isinstance(t, dict))
            buy_qty = sum(int(t.get('quantity', 0)) for t in buys if isinstance(t, dict))
            sell_qty = sum(int(t.get('quantity', 0)) for t in sells if isinstance(t, dict))
            
            avg_price = buy_cost / buy_qty if buy_qty > 0 else 0
            current_invested = (buy_qty - sell_qty) * avg_price
            
            try: m_cap = float(stock.get('MarketCap', 0)) / 10000
            except: m_cap = 0
            
            portfolio_list.append({
                'id': stock['Symbol'], 'name': stock['Name'],
                'invested': current_invested, 'budget': m_cap,
                'progress': (current_invested / m_cap * 100) if m_cap > 0 else 0,
                'strategy': str(stock.get('Category', 'Long')).strip()
            })
            total_invested += current_invested
            total_budget += m_cap

        # 헤더 렌더링
        col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
        with col_h1:
            st.subheader("📊 포트폴리오 요약")
            c_s1, c_s2 = st.columns(2)
            with c_s1: portfolio_summary_card("총 예산", total_budget)
            with c_s2: portfolio_summary_card("진행률", (total_invested / total_budget * 100) if total_budget > 0 else 0, is_percent=True)
        
        with col_h2:
            st.write("") # 여백
            st.write("")
            split_strategy = st.selectbox("투자전략 필터", ["전체", "Long", "Short", "Macro"], key="split_filter")
            if split_strategy != "전체":
                portfolio_list = [p for p in portfolio_list if p['strategy'] == split_strategy]
        
        with col_h3:
            st.write("") # 여백
            st.write("")
            with st.expander("➕ 종목 관리"):
                # 간단한 추가 폼
                with st.form("quick_add"):
                    q_symbol = st.text_input("티커 (예: AAPL)")
                    q_name = st.text_input("종목명")
                    q_mcap = st.number_input("시총(억원)", min_value=0)
                    q_installments = st.number_input("분할횟수", min_value=1, value=3, step=1)
                    q_strategy = st.selectbox("투자전략", ["Long", "Short", "Macro"])
                    if st.form_submit_button("추가"):
                        if q_symbol and q_name:
                            # Symbol 정규화 (숫자만인 경우 6자리 0패딩)
                            q_sym_norm = q_symbol.strip().upper()
                            if q_sym_norm.isdigit():
                                q_sym_norm = q_sym_norm.zfill(6)

                            # 기존 종목 중복 확인 (관심종목 포함)
                            existing_symbols = df_all['Symbol'].astype(str).str.strip().str.upper()
                            dup_mask = existing_symbols == q_sym_norm

                            if dup_mask.any():
                                # 기존 종목 활용: Installments와 Category(투자전략)만 업데이트
                                idx = df_all[dup_mask].index[0]
                                df_all.at[idx, 'Installments'] = int(q_installments)
                                df_all.at[idx, 'Category'] = q_strategy
                                existing_name = str(df_all.at[idx, 'Name'])
                                save_stocks(df_all)
                                st.success(f"기존 종목 '{existing_name}'을 플래너에 추가했습니다.")
                            else:
                                # 완전히 새로운 종목 추가
                                new_stock = {
                                    "Symbol": q_sym_norm,
                                    "Name": q_name,
                                    "MarketCap": q_mcap * 100000000,
                                    "Installments": int(q_installments),
                                    "Category": q_strategy,
                                    "BuyTransactions": "[]",
                                    "SellTransactions": "[]"
                                }
                                save_stocks(pd.concat([df_all, pd.DataFrame([new_stock])], ignore_index=True))
                                st.success(f"'{q_name}' 종목이 추가되었습니다.")
                            st.rerun()

        # 도넛 차트 - 필터링 후 portfolio_list 기준으로 재계산 (필터/삭제 후 불일치 방지)
        pie_data = [p for p in portfolio_list if p['invested'] > 0]
        if pie_data:
            fig_donut = px.pie(pd.DataFrame(pie_data), values='invested', names='name', hole=0.6, title="자산 비중")
            fig_donut.update_layout(
                paper_bgcolor='rgba(46, 46, 46, 0.9)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#ffffff', size=13, family='Pretendard'),
                title=dict(
                    text="자산 비중",
                    font=dict(color='#ffffff', size=16, family='Pretendard'),
                    x=0.5, xanchor='center'
                ),
                legend=dict(
                    font=dict(color='#ffffff', size=12, family='Pretendard'),
                    bgcolor='rgba(255,255,255,0.05)',
                    bordercolor='rgba(255,255,255,0.15)',
                    borderwidth=1,
                )
            )
            fig_donut.update_traces(
                textfont=dict(color='#ffffff', size=13),
                textinfo='percent+label'
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        # 종목 뱃지 그리드
        st.markdown("### 종목별 현황")
        sorted_portfolio = sorted(portfolio_list, key=lambda x: x['name'])
        cols = st.columns(6)
        for i, p in enumerate(sorted_portfolio):
            with cols[i % 6]:
                create_overlay_badge(p['name'], p['progress'], f"badge_{p['id']}", show_stock_detail_modal, p['id'])

        # 전체 현황판 - Streamlit columns 기반 카드 그리드
        with st.expander("📋 전체 현황판", expanded=True):
            if sorted_portfolio:
                strategy_color_map = {'Long': '#3b82f6', 'Short': '#ef4444', 'Macro': '#8b5cf6'}
                COLS = 3  # 한 행에 카드 몇 개
                rows = [sorted_portfolio[i:i+COLS] for i in range(0, len(sorted_portfolio), COLS)]
                for row_items in rows:
                    col_objs = st.columns(COLS)
                    for col, p in zip(col_objs, row_items):
                        progress_val = min(100, max(0, float(p['progress'])))
                        strategy = str(p.get('strategy', 'Long'))
                        strategy_color = strategy_color_map.get(strategy, '#6b7280')

                        if progress_val >= 80:
                            bar_color = '#10b981'
                            bar_glow = 'rgba(16,185,129,0.45)'
                        elif progress_val >= 50:
                            bar_color = '#6366f1'
                            bar_glow = 'rgba(99,102,241,0.45)'
                        else:
                            bar_color = '#f59e0b'
                            bar_glow = 'rgba(245,158,11,0.45)'

                        budget_display = f"₩{p['budget']:,.0f}" if p['budget'] > 0 else "미설정"

                        with col:
                            st.markdown(f"""
                            <div style="
                                background:rgba(255,255,255,0.05);
                                border:1px solid rgba(255,255,255,0.12);
                                border-radius:14px;
                                padding:1.2rem;
                                margin-bottom:0.6rem;
                                box-shadow:0 4px 15px rgba(0,0,0,0.25);
                            ">
                                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.8rem;">
                                    <span style="color:#ffffff;font-weight:700;font-size:0.97rem;">{p['name']}</span>
                                    <span style="background:{strategy_color};color:#fff;padding:0.12rem 0.6rem;border-radius:20px;font-size:0.7rem;font-weight:700;">{strategy}</span>
                                </div>
                                <div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">
                                    <span style="color:rgba(255,255,255,0.4);font-size:0.75rem;">투자금액</span>
                                    <span style="color:rgba(255,255,255,0.4);font-size:0.75rem;">예산</span>
                                </div>
                                <div style="display:flex;justify-content:space-between;margin-bottom:0.9rem;">
                                    <span style="color:#ffffff;font-size:0.92rem;font-weight:600;">₩{p['invested']:,.0f}</span>
                                    <span style="color:rgba(255,255,255,0.55);font-size:0.88rem;">{budget_display}</span>
                                </div>
                                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.35rem;">
                                    <span style="color:rgba(255,255,255,0.4);font-size:0.75rem;">매수 진행률</span>
                                    <span style="color:{bar_color};font-weight:700;font-size:0.9rem;">{progress_val:.1f}%</span>
                                </div>
                                <div style="background:rgba(255,255,255,0.12);border-radius:100px;height:10px;overflow:hidden;">
                                    <div style="background:linear-gradient(90deg,{bar_color},{bar_color}99);width:{progress_val:.2f}%;height:100%;border-radius:100px;box-shadow:0 0 8px {bar_glow};"></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("표시할 종목이 없습니다.")


# === 메인 화면 - 탭 구조 ===
tab1, tab2 = st.tabs(["📈 주식 추적기", "💰 분할 매수 플래너"])

with tab1:
    render_tracker_tab()

with tab2:
    render_planner_tab()

import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import datetime, timedelta

# FinanceDataReader 선택적 임포트
try:
    import FinanceDataReader as fdr
    FDR_AVAILABLE = True
except ImportError:
    FDR_AVAILABLE = False
    fdr = None

# 주가 데이터 가져오기 (하이브리드 방식: FinanceDataReader + yfinance)
@st.cache_data(ttl=7200)  # 2시간 캐싱
def get_stock_data(symbol):
    if symbol is None:
        return None
    
    try:
        if isinstance(symbol, (int, float)):
            symbol_str = str(int(symbol)).zfill(6)
        else:
            symbol_str = str(symbol).strip()
        
        if not symbol_str:
            return None
    except Exception:
        return None
    
    max_retries = 3
    retry_delay = 2
    
    clean_symbol = symbol_str.upper()
    is_korean = False
    market_suffix = None
    
    if clean_symbol.endswith('.KS') or clean_symbol.endswith('.KQ'):
        market_suffix = '.KS' if clean_symbol.endswith('.KS') else '.KQ'
        temp_symbol = clean_symbol.replace('.KS', '').replace('.KQ', '')
        if temp_symbol.isdigit():
            clean_symbol = temp_symbol.zfill(6)
            is_korean = True
    elif clean_symbol.isdigit():
        clean_symbol = clean_symbol.zfill(6)
        is_korean = True
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(retry_delay * (attempt + 1))
            
            df = None
            
            if is_korean and FDR_AVAILABLE:
                try:
                    df = fdr.DataReader(clean_symbol)
                    if df is not None and not df.empty:
                        if df.index.name is None or df.index.name != 'Date':
                            df.index.name = 'Date'
                except Exception:
                    df = None
            
            if df is None or df.empty:
                yf_symbol = symbol_str
                if is_korean:
                    if market_suffix:
                        yf_symbol = clean_symbol + market_suffix
                        df = yf.Ticker(yf_symbol).history(period="max")
                    else:
                        yf_symbol = clean_symbol + '.KS'
                        df = yf.Ticker(yf_symbol).history(period="max")
                        if df is None or df.empty:
                            yf_symbol = clean_symbol + '.KQ'
                            df = yf.Ticker(yf_symbol).history(period="max")
                else:
                    df = yf.Ticker(yf_symbol).history(period="max")
            
            if df is None or df.empty:
                continue
            
            if df.index.name != 'Date':
                df.index.name = 'Date'
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            df.index = pd.to_datetime(df.index).normalize()
            
            column_mapping = {}
            for col in df.columns:
                col_lower = str(col).lower()
                if col_lower in ['open', '시가']: column_mapping[col] = 'Open'
                elif col_lower in ['high', '고가']: column_mapping[col] = 'High'
                elif col_lower in ['low', '저가']: column_mapping[col] = 'Low'
                elif col_lower in ['close', '종가']: column_mapping[col] = 'Close'
                elif col_lower in ['volume', '거래량']: column_mapping[col] = 'Volume'
            
            if column_mapping:
                df = df.rename(columns=column_mapping)
            
            return df
            
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return None
    return None

# 당일 상승률 계산 함수
@st.cache_data(ttl=300)  # 5분 캐싱
def get_daily_change(symbol):
    try:
        time.sleep(1.0)
        stock_df = get_stock_data(symbol)
        if stock_df is None or stock_df.empty or len(stock_df) < 2:
            return None
        
        latest = stock_df.iloc[-1]
        previous = stock_df.iloc[-2]
        
        prev_close = previous['Close']
        curr_close = latest['Close']
        
        if pd.isna(prev_close) or pd.isna(curr_close) or prev_close == 0:
            return None
        
        return ((curr_close - prev_close) / prev_close) * 100
    except Exception:
        return None

# 주80 이동평균선 조건 체크 함수
@st.cache_data(ttl=3600)  # 1시간 캐싱
def check_week80_condition(symbol):
    try:
        df = get_stock_data(symbol)
        if df is None or df.empty:
            return False
            
        weekly_df = df.resample('W').last()
        if len(weekly_df) < 80:
            return False
            
        weekly_df['MA80'] = weekly_df['Close'].rolling(window=80).mean()
        ma80 = weekly_df['MA80'].dropna().iloc[-1]
        
        if pd.isna(ma80) or ma80 == 0:
            return False
            
        recent_days = df.iloc[-3:]
        for _, row in recent_days.iterrows():
            close_price = row['Close']
            if pd.isna(close_price) or close_price == 0:
                continue
            if abs(close_price - ma80) / ma80 <= 0.1:
                return True
        return False
    except Exception:
        return False

# 날짜 문자열을 datetime으로 변환하고 정규화하는 함수
def parse_date_safe(date_str):
    if pd.isna(date_str) or date_str == "" or str(date_str).strip() == "":
        return None
    try:
        # 문자열을 datetime으로 변환하고 날짜만 남기기 (시간 정보 제거)
        date_dt = pd.to_datetime(date_str).normalize()
        return date_dt
    except Exception:
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

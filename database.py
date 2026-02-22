import streamlit as st
import pandas as pd
import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials

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
        expected_columns = ["Symbol", "Name", "InterestDate", "Note", "MarketCap", "Installments", "Category", "BuyTransactions", "SellTransactions", "ChangeRate", "Week80Gap"]
        
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
        
        # get_all_values() 사용: 모든 값을 문자열로 유지 (000123 → "000123" 보존)
        # get_all_records()는 숫자처럼 보이는 값을 정수로 자동변환하므로 사용 안 함
        all_values = worksheet.get_all_values()

        expected_columns = ["Symbol", "Name", "InterestDate", "Note", "MarketCap",
                            "Installments", "Category", "BuyTransactions", "SellTransactions", "ChangeRate", "Week80Gap"]

        if len(all_values) <= 1:
            # 헤더만 있거나 완전히 빈 경우
            return pd.DataFrame(columns=expected_columns)

        headers = all_values[0]
        data = all_values[1:]

        # DataFrame으로 변환 (모든 값 문자열 유지)
        df = pd.DataFrame(data, columns=headers)

        # 없는 컬럼 추가
        for col in expected_columns:
            if col not in df.columns:
                df[col] = ""

        # 빈 문자열 → NA 처리
        df = df.replace("", pd.NA)

        # Symbol 컬럼: 항상 문자열로 유지 (앞의 0 보존)
        if 'Symbol' in df.columns:
            df['Symbol'] = df['Symbol'].astype(str).str.strip()
            df.loc[df['Symbol'] == 'nan', 'Symbol'] = pd.NA

        return df
    except Exception as e:
        st.error(f"❌ 데이터 로드 실패: {str(e)}")
        # 빈 DataFrame 반환
        columns = ["Symbol", "Name", "InterestDate", "Note", "MarketCap", "Installments", "Category", "BuyTransactions", "SellTransactions", "ChangeRate", "Week80Gap"]
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
        existing_df = load_stocks()
        change_rate_map = {}
        if 'ChangeRate' in existing_df.columns and 'Symbol' in existing_df.columns:
            for _, row in existing_df.iterrows():
                symbol = row.get('Symbol', '')
                change_rate = row.get('ChangeRate', '')
                if symbol and pd.notna(change_rate) and change_rate != '':
                    change_rate_map[str(symbol)] = change_rate
        
        # 빈 값 처리
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
        
        # 기존 ChangeRate 값 복원
        if 'Symbol' in df.columns:
            df['ChangeRate'] = df.apply(
                lambda row: change_rate_map.get(str(row['Symbol']), row.get('ChangeRate', '')),
                axis=1
            )
        
        # 헤더 포함 전체 데이터 준비
        values = [df.columns.tolist()] + df.values.tolist()
        
        # 기존 데이터 지우고 새 데이터 쓰기
        # RAW 모드: 000123 같은 값을 숫자로 자동 변환하지 않고 문자열로 저장
        worksheet.clear()
        worksheet.update(values, value_input_option='RAW')
        
        # 캐시 무효화
        load_stocks.clear()
        
    except Exception as e:
        st.error(f"❌ 데이터 저장 실패: {str(e)}")
        raise

# 분할 매수 플래너 데이터 로드 (통합 시트 사용)
@st.cache_data(ttl=60)
def load_split_purchase_data():
    """통합 Stocks 시트에서 분할 매수 플래너 데이터를 로드합니다."""
    return load_stocks()

# 분할 매수 플래너 데이터 저장 (통합 시트 사용)
def save_split_purchase_data(df):
    """통합 Stocks 시트에 분할 매수 플래너 데이터를 저장합니다."""
    save_stocks(df)

# 주식 추적기 (Stock Tracker) - Project Guide

## 📌 프로젝트 개요
Google Sheets를 데이터베이스로 활용하여 관심 종목과 매수 종목을 추적하고, 분할 매수 계획을 세우며 관리하는 맞춤형 개인 주식 트레이딩 대시보드 애플리케이션입니다. Streamlit을 기반으로 구현되어 있습니다.

## 📂 폴더 및 파일 구조 (리팩토링 완료)

기존 Monolithic 구조에서 관심사 분리(SoC) 원칙에 따라 다음과 같이 모듈화되었습니다:

```text
c:\Users\alcls\OneDrive\바탕 화면\Stock\주식추적기\
├── app.py                 # 메인 애플리케이션 UI 흐름 및 탭 제어 (슬림화 완료)
├── database.py            # Google Sheets API 연동 및 CRUD 로직 전담
├── stock_utils.py         # 주가 데이터 수집(yfinance, FDR) 및 기술적 지표 계산
├── ui_styles.py           # 커스텀 CSS 스타일링 및 테마 관리
├── ui_components.py       # 뱃지, 카드 등 재사용 가능한 UI 컴포넌트
├── secrets.json           # Google Sheets API 인증 정보
└── (데이터 파일들)         # stocks.csv, Integrated_Stock_DB 등
```

## 🏗️ 모듈별 주요 역할

### 1. `app.py` (Main Interface)
- **역할**: 사용자 입력을 받고 각 탭(추적기, 플래너)의 전체 레이아웃을 렌더링합니다.
- **개선사항**: 약 3,600줄의 코드를 1,300줄 수준으로 최적화하여 가독성과 유지보수성을 대폭 향상했습니다.

### 2. `database.py` (Persistence Layer)
- **핵심 함수**: `load_stocks()`, `save_stocks()`, `load_split_purchase_data()`
- **역할**: Google Sheets와의 통신을 전담하며, 데이터의 JSON 파싱 및 보존 로직을 포함합니다.

### 3. `stock_utils.py` (Logic Layer)
- **핵심 함수**: `get_stock_data()`, `check_week80_condition()`, `find_trading_date()`
- **역할**: 국내/해외 주가 API를 호출하고, '주80 이격도' 등 기술적 분석 지표를 계산합니다.

### 4. `ui_styles.py` & `ui_components.py` (Presentation Layer)
- **역할**: 모던 핀테크 스타일의 다크 테마 CSS와 복잡한 UI 요소(진행률 뱃지, 요약 카드)를 생성합니다.
- **UI 특징**: 
  - `.dashboard-header`: 필터 영역을 별도 컨테이너로 그룹화하여 일체감 부여.
  - `.content-card`: 주요 차트와 정보를 카드 형태로 시각화.
  - 진행률 뱃지: 종목별 매수 진행률을 배경 그라데이션으로 직관적 표시.

## 🚀 UI/UX 개선 사항 (2026-02-22)

1.  **필터 섹션 그룹화**: 상단 컨트롤 바를 `dashboard-header` 스타일로 묶어 대시보드 느낌을 강화했습니다.
2.  **종목 상세 메트릭**: 단일 종목 조회 시 현재가, 변동폭, 최고/최저가, 거래량을 상단에 배치했습니다.
3.  **플래너 최적화**: 분할 매수 플래너의 데이터 로딩 방식을 효율화하고, 요약 정보를 상단 카드 형태로 재구성했습니다.
4.  **테마 일관성**: 기존의 노란색 계열 '정보 수정' 영역을 다크 핀테크 테마(Indigo/Dark Blue)에 맞춰 통일했습니다.
5.  **차트 시인성**: Plotly 차트를 컨텐츠 카드 내부에 배치하고 마우스 휠 줌 등 사용자 편의 기능을 활성화했습니다.

## 🛠️ 유지보수 가이드
- **스타일 수정**: UI의 색상이나 폰트를 바꾸려면 `ui_styles.py`를 수정하세요.
- **새로운 지표 추가**: 주가 분석 로직을 추가하려면 `stock_utils.py`에 함수를 정의하세요.
- **DB 스키마 변경**: Google Sheets의 컬럼 구조를 바꾸려면 `database.py`의 헤더 정의를 수정하세요.

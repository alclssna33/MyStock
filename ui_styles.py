import streamlit as st

def inject_custom_css():
    """애플리케이션에 커스텀 CSS를 주입합니다."""
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
    
    /* === 4-1. 입력 필드 높이 통일 (상단 컨트롤 바 정렬) === */
    /* Selectbox 높이 통일 */
    div[data-baseweb="select"] > div {
        min-height: 38px !important;
        height: 38px !important;
        display: flex !important;
        align-items: center !important;
    }
    
    /* Date Input 높이 통일 */
    input[type="date"],
    input[type="text"],
    div[data-baseweb="input"] input {
        min-height: 38px !important;
        height: 38px !important;
        padding: 0 0.75rem !important;
    }
    
    /* Date Input 컨테이너 높이 통일 */
    div[data-baseweb="input"] {
        min-height: 38px !important;
        height: 38px !important;
    }
    
    div[data-baseweb="input"] > div {
        min-height: 38px !important;
        height: 38px !important;
    }
    
    /* Label 위치 조정 (모든 입력 필드의 라벨을 상단에 고정) */
    label {
        margin-bottom: 0.3rem !important;
    }
    
    /* Streamlit column 내부 컨테이너 정렬 */
    div[data-testid="column"] > div {
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-end !important;
    }
    
    /* Radio 버튼 및 Checkbox 높이 조정 */
    div[role="radiogroup"] {
        min-height: 38px !important;
        display: flex !important;
        align-items: flex-end !important;
    }
    
    /* Checkbox 컨테이너 정렬 */
    div[data-testid="stCheckbox"] {
        min-height: 38px !important;
        display: flex !important;
        align-items: flex-end !important;
        padding-bottom: 0 !important;
    }


    /* === 5. 버튼 스타일 (수정됨: 실제 DOM 구조에 맞춤) === */
    
    /* [1. 공통 베이스] 모든 버튼 텍스트 색상 강제 */
    button,
    button p,
    button span {
        color: #FFFFFF !important;
    }
    
    /* [2. 기본 버튼] 모든 버튼에 먼저 적용 (보라색 - Default) */
    .stButton > button,
    div[data-testid="stDialog"] button,
    div[data-testid="stForm"] button,
    div[role="dialog"] button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button p,
    div[data-testid="stDialog"] button p,
    div[data-testid="stForm"] button p {
        color: #FFFFFF !important;
    }
    
    /* 기본 버튼 호버 효과 */
    .stButton > button:hover,
    div[data-testid="stDialog"] button:hover,
    div[data-testid="stForm"] button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4) !important;
    }
    
    /* [3. Secondary 버튼] 파란색 - 수정/취소 (실제 DOM 속성 사용) */
    button[data-testid="stBaseButton-secondaryFormSubmit"],
    button[kind="secondaryFormSubmit"],
    .stButton > button[data-testid="stBaseButton-secondaryFormSubmit"],
    .stButton > button[kind="secondaryFormSubmit"],
    div[data-testid="stDialog"] button[data-testid="stBaseButton-secondaryFormSubmit"],
    div[data-testid="stDialog"] button[kind="secondaryFormSubmit"],
    div[data-testid="stForm"] button[data-testid="stBaseButton-secondaryFormSubmit"],
    div[data-testid="stForm"] button[kind="secondaryFormSubmit"],
    div[role="dialog"] button[data-testid="stBaseButton-secondaryFormSubmit"],
    div[role="dialog"] button[kind="secondaryFormSubmit"] {
        background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%) !important;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #FFFFFF !important;
    }
    button[data-testid="stBaseButton-secondaryFormSubmit"]:hover,
    button[kind="secondaryFormSubmit"]:hover,
    .stButton > button[data-testid="stBaseButton-secondaryFormSubmit"]:hover,
    .stButton > button[kind="secondaryFormSubmit"]:hover,
    div[data-testid="stDialog"] button[data-testid="stBaseButton-secondaryFormSubmit"]:hover,
    div[data-testid="stDialog"] button[kind="secondaryFormSubmit"]:hover,
    div[data-testid="stForm"] button[data-testid="stBaseButton-secondaryFormSubmit"]:hover,
    div[data-testid="stForm"] button[kind="secondaryFormSubmit"]:hover,
    div[role="dialog"] button[data-testid="stBaseButton-secondaryFormSubmit"]:hover,
    div[role="dialog"] button[kind="secondaryFormSubmit"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(59, 130, 246, 0.4) !important;
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
    }
    button[data-testid="stBaseButton-secondaryFormSubmit"] p,
    button[kind="secondaryFormSubmit"] p,
    div[data-testid="stDialog"] button[data-testid="stBaseButton-secondaryFormSubmit"] p,
    div[data-testid="stDialog"] button[kind="secondaryFormSubmit"] p {
        color: #FFFFFF !important;
    }
    
    /* [4. Primary 버튼] 빨간색 - 기록/삭제/추가 (실제 DOM 속성 사용) */
    button[data-testid="stBaseButton-primaryFormSubmit"],
    button[kind="primaryFormSubmit"],
    .stButton > button[data-testid="stBaseButton-primaryFormSubmit"],
    .stButton > button[kind="primaryFormSubmit"],
    div[data-testid="stDialog"] button[data-testid="stBaseButton-primaryFormSubmit"],
    div[data-testid="stDialog"] button[kind="primaryFormSubmit"],
    div[data-testid="stForm"] button[data-testid="stBaseButton-primaryFormSubmit"],
    div[data-testid="stForm"] button[kind="primaryFormSubmit"],
    div[role="dialog"] button[data-testid="stBaseButton-primaryFormSubmit"],
    div[role="dialog"] button[kind="primaryFormSubmit"] {
        background: linear-gradient(135deg, #ef4444 0%, #f87171 100%) !important;
        box-shadow: 0 4px 6px rgba(239, 68, 68, 0.3) !important;
        border: none !important;
        color: #FFFFFF !important;
    }
    button[data-testid="stBaseButton-primaryFormSubmit"]:hover,
    button[kind="primaryFormSubmit"]:hover,
    .stButton > button[data-testid="stBaseButton-primaryFormSubmit"]:hover,
    .stButton > button[kind="primaryFormSubmit"]:hover,
    div[data-testid="stDialog"] button[data-testid="stBaseButton-primaryFormSubmit"]:hover,
    div[data-testid="stDialog"] button[kind="primaryFormSubmit"]:hover,
    div[data-testid="stForm"] button[data-testid="stBaseButton-primaryFormSubmit"]:hover,
    div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover,
    div[role="dialog"] button[data-testid="stBaseButton-primaryFormSubmit"]:hover,
    div[role="dialog"] button[kind="primaryFormSubmit"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(239, 68, 68, 0.4) !important;
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%) !important;
    }
    button[data-testid="stBaseButton-primaryFormSubmit"] p,
    button[kind="primaryFormSubmit"] p,
    div[data-testid="stDialog"] button[data-testid="stBaseButton-primaryFormSubmit"] p,
    div[data-testid="stDialog"] button[kind="primaryFormSubmit"] p {
        color: #FFFFFF !important;
    }
    
    /* === 뱃지 오버레이 버튼 숨기기 (종목별 현황) === */
    /* 뱃지가 있는 컨테이너 다음에 오는 버튼 컨테이너 타겟팅 */
    div[data-testid="stMarkdownContainer"]:has(.badge-overlay-visual) + div[data-testid="stButton"],
    div[data-testid="stMarkdownContainer"]:has(.badge-overlay-visual) ~ div[data-testid="stButton"],
    div:has(.badge-overlay-visual) + div[data-testid="stButton"],
    div:has(.badge-overlay-visual) ~ div[data-testid="stButton"] {
        margin-top: -48px !important;
        position: relative !important;
        z-index: 10 !important;
        pointer-events: auto !important;
    }
    
    /* 뱃지 오버레이 버튼 완전히 투명하게 */
    div[data-testid="stMarkdownContainer"]:has(.badge-overlay-visual) + div[data-testid="stButton"] button,
    div[data-testid="stMarkdownContainer"]:has(.badge-overlay-visual) ~ div[data-testid="stButton"] button,
    div:has(.badge-overlay-visual) + div[data-testid="stButton"] button,
    div:has(.badge-overlay-visual) ~ div[data-testid="stButton"] button {
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
        pointer-events: auto !important;
    }
    
    /* 뱃지 시각적 요소는 클릭 불가 (버튼이 클릭 처리) */
    .badge-overlay-visual {
        pointer-events: none !important;
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
    /* 사이드바 버튼 - 기본 스타일 (data-testid 기반) */
    section[data-testid="stSidebar"] button:not([data-testid="baseButton-primary"]):not([data-testid="baseButton-secondary"]) {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: #FFFFFF !important;
    }

    /* === 7. '정보 수정하기' Expander 스타일 (레거시 - 16번 섹션으로 대체됨) === */
    /* 이전 .streamlit-expanderHeader 스타일은 16번 섹션 [data-testid="stExpander"]로 대체 */
    
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
    
    /* [5. 개별 버튼 스타일링] 필요시 아래에 특정 버튼만 추가 가능 */
    /* 예시:
    button[key="delete_button"] {
        background: linear-gradient(135deg, #ef4444 0%, #f87171 100%) !important;
        color: #FFFFFF !important;
    }
    */
    
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
    
    /* Dialog 내부 모든 텍스트 - 흰색 (버튼과 입력 필드 제외) */
    div[data-testid="stDialog"] *:not(button):not(button *):not(input):not(input *):not(textarea):not(textarea *),
    div[role="dialog"] *:not(button):not(button *):not(input):not(input *):not(textarea):not(textarea *),
    section[data-testid="stDialog"] *:not(button):not(button *):not(input):not(input *):not(textarea):not(textarea *),
    section[role="dialog"] *:not(button):not(button *):not(input):not(input *):not(textarea):not(textarea *) {
        color: #FFFFFF !important;
    }
    
    /* Dialog 내부 입력 필드 텍스트 색상 강제 (전역 스타일보다 우선) */
    div[data-testid="stDialog"] input,
    div[data-testid="stDialog"] textarea,
    div[data-testid="stDialog"] input *,
    div[data-testid="stDialog"] textarea *,
    div[role="dialog"] input,
    div[role="dialog"] textarea,
    div[role="dialog"] input *,
    div[role="dialog"] textarea * {
        color: #000000 !important;
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
    
    /* Dialog 내부 기본 버튼 - Primary/Secondary가 아닌 경우만 (data-testid 기반) */
    div[data-testid="stDialog"] .stButton > button:not([data-testid="baseButton-primary"]):not([data-testid="baseButton-secondary"]):not([type="submit"]),
    div[role="dialog"] .stButton > button:not([data-testid="baseButton-primary"]):not([data-testid="baseButton-secondary"]):not([type="submit"]) {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
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
    /* === 11. 대시보드 헤더 스타일 === */
    .dashboard-header {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    /* === 12. 컨텐츠 카드 스타일 === */
    .content-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 15px;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 1.5rem;
    }

    /* === 13. 탭(Tab) 스타일 === */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        padding: 0.3rem !important;
        gap: 0.3rem !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: rgba(255, 255, 255, 0.55) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        background: transparent !important;
        padding: 0.5rem 1.5rem !important;
        transition: all 0.2s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff !important;
        background: rgba(255, 255, 255, 0.08) !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4) !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] p,
    .stTabs [data-baseweb="tab"][aria-selected="true"] span {
        color: #ffffff !important;
    }
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] span {
        color: inherit !important;
    }
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* === 14. Metric 델타 색상 보존 === */
    /* 상승 델타 (초록) */
    [data-testid="stMetricDelta"] svg[data-testid="stMetricDeltaIcon-Up"],
    [data-testid="stMetricDeltaIcon-Up"] {
        color: #10b981 !important;
        fill: #10b981 !important;
    }
    /* 하락 델타 (빨강) */
    [data-testid="stMetricDelta"] svg[data-testid="stMetricDeltaIcon-Down"],
    [data-testid="stMetricDeltaIcon-Down"] {
        color: #ef4444 !important;
        fill: #ef4444 !important;
    }
    /* Metric 컨테이너 전체 */
    [data-testid="stMetricValue"] > div,
    [data-testid="stMetricValue"] label,
    [data-testid="stMetricLabel"] > div,
    [data-testid="stMetricLabel"] label {
        color: #ffffff !important;
    }
    /* Metric delta 텍스트 - Streamlit inline style 우선 적용 */
    [data-testid="stMetricDelta"] > div {
        /* color는 override하지 않음 - inline style이 적용됨 */
        font-weight: 600 !important;
    }

    /* === 15. Alert / 알림 메시지 스타일 === */
    /* Success */
    [data-testid="stAlert"][data-baseweb="notification"] {
        border-radius: 10px !important;
    }
    div[data-testid="stAlert"] {
        border-radius: 10px !important;
    }
    /* 알림 메시지 내부 텍스트 - 배경에 따라 자동 처리 */
    div[data-testid="stAlert"] p,
    div[data-testid="stAlert"] span:not(svg span) {
        color: inherit !important;
    }

    /* === 16. Expander 스타일 (data-testid 기반 - 최신 Streamlit) === */
    [data-testid="stExpander"] {
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 12px !important;
        overflow: visible !important;   /* hidden → visible: 내부 카드 잘림 방지 */
        background: rgba(20, 25, 50, 0.5) !important;
        margin-bottom: 0.8rem !important;
    }
    /* Expander 헤더 (summary 태그) */
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] > details > summary {
        background: linear-gradient(135deg, #312e81 0%, #1e1b4b 100%) !important;
        padding: 0.9rem 1.2rem !important;
        border-radius: 12px 12px 0 0 !important;
    }
    [data-testid="stExpander"] summary:hover {
        background: linear-gradient(135deg, #3730a3 0%, #312e81 100%) !important;
    }
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] summary div {
        color: #e0e7ff !important;
        font-weight: 600 !important;
    }
    [data-testid="stExpander"] summary svg {
        fill: #e0e7ff !important;
        color: #e0e7ff !important;
    }
    /* Expander 내용 영역 */
    [data-testid="stExpanderDetails"] {
        background: rgba(30, 41, 59, 0.3) !important;
        border-top: 1px solid rgba(99, 102, 241, 0.2) !important;
        padding: 1rem 1.2rem !important;
        overflow: visible !important;
    }

    /* === 17. 현황판 카드 스타일 === */
    .portfolio-card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 1rem;
        padding: 0.5rem 0;
    }
    .portfolio-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 1.3rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .portfolio-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }
    .progress-bar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 100px;
        height: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

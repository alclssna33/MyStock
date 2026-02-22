import streamlit as st
import json
import re

def create_overlay_badge(name, progress, key, callback, *args, dark_color=None, light_color=None):
    """진행률 그라데이션 배지 버튼 - CSS :has() 선택자로 st.button에 직접 스타일 주입

    dark_color / light_color: 전략별 색상 오버라이드 (기본: 초록)
    """
    progress_pct = min(100, max(0, progress))
    dark_green = dark_color if dark_color else '#10b981'
    light_green = light_color if light_color else '#86efac'
    gradient = f'linear-gradient(to right, {dark_green} 0%, {dark_green} {progress_pct}%, {light_green} {progress_pct}%, {light_green} 100%)'

    # CSS ID에 안전한 문자만 허용 (점·슬래시 등 특수문자 → 하이픈)
    marker_id = "btn-marker-" + re.sub(r'[^a-zA-Z0-9\-]', '-', key)

    # 숨겨진 마커 span + CSS :has()로 바로 다음 형제 stElementContainer의 버튼에 그라데이션 주입
    st.markdown(f"""
    <span id="{marker_id}" style="display:none;"></span>
    <style>
        [data-testid="stElementContainer"]:has(#{marker_id}) + [data-testid="stElementContainer"] [data-testid="stButton"] button,
        [data-testid="stElementContainer"]:has(#{marker_id}) + [data-testid="stElementContainer"] [data-testid="stButton"] button:focus {{
            background: {gradient} !important;
            border: 2px solid {dark_green} !important;
            border-radius: 12px !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 0.92rem !important;
            min-height: 52px !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
            transition: all 0.25s ease !important;
        }}
        [data-testid="stElementContainer"]:has(#{marker_id}) + [data-testid="stElementContainer"] [data-testid="stButton"] button:hover {{
            opacity: 0.88 !important;
            box-shadow: 0 6px 16px rgba(16,185,129,0.5) !important;
            transform: translateY(-1px) !important;
        }}
        [data-testid="stElementContainer"]:has(#{marker_id}) + [data-testid="stElementContainer"] [data-testid="stButton"] button p {{
            color: #ffffff !important;
            font-weight: 700 !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    if st.button(name, key=key, use_container_width=True):
        callback(*args)

def portfolio_summary_card(label, value, is_percent=False):
    """포트폴리오 요약 카드 (총 예산, 진행률 등)"""
    bg_gradient = "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)"
    border_color = "#10b981"
    
    st.markdown(f"""
    <div style="
        background: {bg_gradient};
        border: 2px solid {border_color};
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(99, 102, 241, 0.3);
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    ">
        <div style="color: rgba(255, 255, 255, 0.9); font-size: 0.9rem; margin-bottom: 0.5rem;">{label}</div>
        <div style="color: #ffffff; font-size: 1.8rem; font-weight: 700;">
            {f"{value:.2f}%" if is_percent else f"₩{value:,.0f}"}
        </div>
    </div>
    """, unsafe_allow_html=True)

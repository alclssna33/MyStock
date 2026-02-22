import streamlit as st
import json

def create_overlay_badge(name, progress, key, callback, *args):
    """CSS 오버레이 기법으로 뱃지 생성 및 클릭 이벤트 처리"""
    progress_pct = min(100, max(0, progress))
    dark_green = '#10b981'
    light_green = '#86efac'
    gradient = f'linear-gradient(to right, {dark_green} 0%, {dark_green} {progress_pct}%, {light_green} {progress_pct}%, {light_green} 100%)'
    
    unique_id = f"badge-{key.replace('_', '-')}"
    badge_text_escaped = name.replace("'", "'").replace('"', '"')
    
    st.markdown(f"""
    <div id="{unique_id}" class="badge-overlay-visual" style="
        background: {gradient};
        border: 2px solid {dark_green};
        border-radius: 12px;
        color: #ffffff;
        font-weight: 600;
        font-size: 0.95rem;
        padding: 0.8rem 1.5rem;
        min-height: 48px;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Pretendard', sans-serif;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        margin-bottom: 0;
        position: relative;
        z-index: 1;
        user-select: none;
        pointer-events: none;
    ">{name}</div>
    <script>
        (function() {{
            const badgeId = '{unique_id}';
            const badgeText = '{badge_text_escaped}';
            
            function hideButton() {{
                const badge = document.getElementById(badgeId);
                if (!badge) return;
                
                let container = badge.closest('[data-testid="stElementContainer"]') || 
                               badge.closest('[data-testid="stVerticalBlock"]') ||
                               badge.closest('[data-testid="column"]');
                if (!container) return;
                
                let sibling = container.nextElementSibling;
                for (let i = 0; i < 5 && sibling; i++) {{
                    const buttonContainer = sibling.querySelector('[data-testid="stButton"]');
                    if (buttonContainer) {{
                        const button = buttonContainer.querySelector('button');
                        if (button) {{
                            const buttonText = button.textContent.trim() || 
                                             button.querySelector('p')?.textContent.trim() || 
                                             button.querySelector('span')?.textContent.trim() || '';
                            
                            if (buttonText === badgeText || buttonText.includes(badgeText)) {{
                                button.style.cssText = 'opacity: 0 !important; background: transparent !important; border: none !important; color: transparent !important; width: 100% !important; height: 53px !important; min-height: 53px !important; padding: 0 !important; margin: 0 !important; margin-top: -53px !important; cursor: pointer !important; position: relative !important; z-index: 99 !important; pointer-events: auto !important;';
                                buttonContainer.style.cssText = 'margin-top: -53px !important; position: relative !important; z-index: 99 !important;';
                                break;
                            }}
                        }}
                    }}
                    sibling = sibling.nextElementSibling;
                }}
            }}
            setTimeout(hideButton, 100);
            const observer = new MutationObserver(hideButton);
            observer.observe(document.body, {{ childList: true, subtree: true }});
        }})();
    </script>
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

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import base64
import html
import re
import time
from dotenv import load_dotenv

load_dotenv()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.scraper import fetch_live_news
from backend.reddit_scraper import fetch_top_reddit_discussions
from backend.discord_reader import fetch_discord_messages
from backend.newsletter_service import NewsletterService
from backend.ai_enricher import AIEnricher
from backend.db_manager import DatabaseManager

st.set_page_config(
    page_title="VADEMECUM HUB NEWS • Radar & Newsletter de IA",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

db = DatabaseManager()
newsletter_service = NewsletterService()

# Inicializar estados de sesión
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

if "selected_tag" not in st.session_state:
    st.session_state["selected_tag"] = "Todos"

if "just_synced" not in st.session_state:
    st.session_state["just_synced"] = False

if "last_updated" not in st.session_state:
    st.session_state["last_updated"] = datetime.now().strftime("%H:%M:%S")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

if "campaign_history" not in st.session_state:
    st.session_state["campaign_history"] = []

st.session_state["favorites"] = db.get_favorites()

def clean_for_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'</?[a-zA-Z][^>]*>', '', text)
    text = re.sub(r'>a\s+ref[^<]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'a\s+href[^<]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = html.escape(text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = text.replace('\n', '<br>')
    return text

LOGO_PATH = os.path.join(CURRENT_DIR, "assets", "logo.jpg")
logo_b64 = ""
if os.path.exists(LOGO_PATH):
    try:
        with open(LOGO_PATH, "rb") as img_f:
            logo_b64 = base64.b64encode(img_f.read()).decode("utf-8")
    except Exception:
        logo_b64 = ""

# --- SIDEBAR VADEMECUM HUB ---
if logo_b64:
    st.sidebar.markdown(f"""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
        <img src="data:image/jpeg;base64,{logo_b64}" style="width: 44px; height: 44px; border-radius: 10px; border: 1px solid #c9a227; object-fit: cover;" />
        <div>
            <div style="font-family: 'Outfit', sans-serif; font-size: 1.15rem; font-weight: 800; color: #f4efe6; letter-spacing: -0.01em;">VADEMECUM HUB</div>
            <div style="font-size: 0.72rem; color: #c9a227; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;">NEWS & INTELLIGENCE</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("""
    <div style="margin-bottom: 12px;">
        <div style="font-family: 'Outfit', sans-serif; font-size: 1.25rem; font-weight: 800; color: #f4efe6;">⚡ VADEMECUM HUB</div>
        <div style="font-size: 0.72rem; color: #c9a227; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;">NEWS & INTELLIGENCE</div>
    </div>
    """, unsafe_allow_html=True)

theme_mode = st.sidebar.radio(
    "🎨 Estilo Visual",
    ["🌙 Vademecum Dark", "☀️ Vademecum Light"],
    index=0 if st.session_state["theme"] == "dark" else 1,
    horizontal=True
)
st.session_state["theme"] = "dark" if "Dark" in theme_mode else "light"
is_dark = st.session_state["theme"] == "dark"

# SISTEMA DE DISEÑO VADEMECUM HUB
if is_dark:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        :root {
            --bg-vademecum: #0e0d0c;
            --surface-vademecum: #161411;
            --border-vademecum: #2e2a24;
            --accent-gold: #c9a227;
            --accent-gold-hover: #e5be38;
            --accent-teal: #2f6f6a;
            --text-ivory: #f4efe6;
            --text-muted: #a8a29e;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background-color: var(--bg-vademecum) !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            color: var(--text-ivory) !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--surface-vademecum) !important;
            border-right: 1px solid var(--border-vademecum) !important;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: var(--text-ivory) !important;
            font-weight: 600 !important;
        }

        div[data-testid="stTextInput"] input,
        .stTextInput input,
        input[type="text"],
        textarea {
            background-color: var(--surface-vademecum) !important;
            color: var(--text-ivory) !important;
            -webkit-text-fill-color: var(--text-ivory) !important;
            border: 1px solid var(--border-vademecum) !important;
            border-radius: 10px !important;
            padding: 10px 16px !important;
            font-size: 0.96rem !important;
            font-weight: 600 !important;
        }

        div[data-testid="stTextInput"] input:focus,
        .stTextInput input:focus,
        input[type="text"]:focus,
        textarea:focus {
            background-color: #211c17 !important;
            border-color: var(--accent-gold) !important;
            box-shadow: 0 0 12px rgba(201, 162, 39, 0.35) !important;
            outline: none !important;
        }

        .vademecum-hero {
            background: radial-gradient(ellipse 90% 80% at 50% -20%, rgba(201, 162, 39, 0.14), transparent 60%),
                        radial-gradient(ellipse 60% 50% at 100% 30%, rgba(47, 111, 106, 0.12), transparent 50%),
                        var(--surface-vademecum);
            border: 1px solid var(--border-vademecum);
            border-radius: 16px;
            padding: 26px 34px;
            margin-bottom: 25px;
            box-shadow: 0 12px 36px rgba(0, 0, 0, 0.55), inset 0 1px 0 rgba(201, 162, 39, 0.25);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 18px;
        }
        .vademecum-eyebrow {
            font-size: 0.75rem;
            color: var(--accent-gold);
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 6px;
        }
        .vademecum-title {
            font-family: 'Outfit', sans-serif;
            font-size: 2.3rem;
            font-weight: 800;
            color: var(--text-ivory);
            margin: 0;
            letter-spacing: -0.02em;
            line-height: 1.1;
        }
        .vademecum-title span {
            color: var(--accent-gold);
        }
        .vademecum-subtitle {
            color: var(--text-muted);
            font-size: 0.98rem;
            margin-top: 8px;
            margin-bottom: 0;
            font-weight: 500;
        }

        .vademecum-dates-box {
            display: flex;
            background: rgba(14, 13, 12, 0.85);
            border: 1px solid var(--border-vademecum);
            border-radius: 12px;
            padding: 10px 18px;
            gap: 16px;
        }
        .vademecum-date-label {
            font-size: 0.70rem;
            text-transform: uppercase;
            color: var(--accent-gold);
            font-weight: 700;
            letter-spacing: 0.06em;
        }
        .vademecum-date-val {
            font-size: 0.95rem;
            font-weight: 800;
            color: var(--text-ivory);
            font-family: 'IBM Plex Mono', monospace;
        }

        .vademecum-kpi-card {
            background: var(--surface-vademecum);
            border: 1px solid var(--border-vademecum);
            border-radius: 14px;
            padding: 20px 22px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .vademecum-kpi-card:hover {
            transform: translateY(-3px);
            border-color: rgba(201, 162, 39, 0.5);
            box-shadow: 0 8px 26px rgba(201, 162, 39, 0.12);
        }
        .vademecum-kpi-label {
            font-size: 0.78rem;
            color: var(--text-muted);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        .vademecum-kpi-value {
            font-size: 1.95rem;
            font-weight: 800;
            color: var(--text-ivory);
            font-family: 'Outfit', sans-serif;
            margin-top: 4px;
        }

        .vademecum-card {
            background: var(--surface-vademecum);
            border: 1px solid var(--border-vademecum);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
        }
        .vademecum-card:hover {
            transform: translateY(-3px);
            border-color: var(--accent-gold);
            box-shadow: 0 10px 32px rgba(201, 162, 39, 0.15);
        }
        
        .badge-source {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-vademecum);
            color: var(--text-muted);
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 600;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-reddit {
            background: rgba(255, 69, 0, 0.15);
            border: 1px solid rgba(255, 69, 0, 0.45);
            color: #ff6e40;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 800;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-discord {
            background: rgba(88, 101, 242, 0.15);
            border: 1px solid rgba(88, 101, 242, 0.45);
            color: #7983f5;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 800;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-category {
            background: rgba(201, 162, 39, 0.12);
            border: 1px solid rgba(201, 162, 39, 0.35);
            color: var(--accent-gold);
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-robotics-category {
            background: linear-gradient(135deg, #c9a227 0%, #b8911f 100%) !important;
            color: #0e0d0c !important;
            padding: 5px 14px !important;
            border-radius: 8px !important;
            font-size: 0.8rem !important;
            font-weight: 800 !important;
            display: inline-block;
            margin-right: 8px;
        }

        .news-title-link {
            font-family: 'Outfit', sans-serif;
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--text-ivory);
            text-decoration: none;
            margin-top: 12px;
            margin-bottom: 10px;
            display: block;
            transition: color 0.2s ease;
        }
        .news-title-link:hover {
            color: var(--accent-gold);
        }
        .news-summary-text {
            color: #d6d0c4;
            font-size: 0.98rem;
            line-height: 1.6;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        :root {
            --bg-vademecum: #fcfaf7;
            --surface-vademecum: #ffffff;
            --border-vademecum: #e7e2d8;
            --accent-gold: #b08a1c;
            --text-dark: #1c1917;
            --text-muted: #78716c;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background-color: var(--bg-vademecum) !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            color: var(--text-dark) !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--surface-vademecum) !important;
            border-right: 1px solid var(--border-vademecum) !important;
        }

        .vademecum-hero {
            background: linear-gradient(135deg, #ffffff 0%, #fdfbf7 50%, #f6f2ea 100%);
            border: 1px solid var(--border-vademecum);
            border-radius: 16px;
            padding: 26px 34px;
            margin-bottom: 25px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 18px;
        }
        .vademecum-eyebrow {
            font-size: 0.75rem;
            color: var(--accent-gold);
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 6px;
        }
        .vademecum-title {
            font-family: 'Outfit', sans-serif;
            font-size: 2.3rem;
            font-weight: 800;
            color: var(--text-dark);
            margin: 0;
            letter-spacing: -0.02em;
            line-height: 1.1;
        }
        .vademecum-title span {
            color: var(--accent-gold);
        }
        .vademecum-subtitle {
            color: var(--text-muted);
            font-size: 0.98rem;
            margin-top: 8px;
            margin-bottom: 0;
            font-weight: 600;
        }

        .vademecum-kpi-card {
            background: var(--surface-vademecum);
            border: 1px solid var(--border-vademecum);
            border-radius: 14px;
            padding: 20px 22px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
        }
        .vademecum-kpi-label {
            font-size: 0.78rem;
            color: var(--text-muted);
            font-weight: 700;
            text-transform: uppercase;
        }
        .vademecum-kpi-value {
            font-size: 1.95rem;
            font-weight: 800;
            color: var(--text-dark);
            font-family: 'Outfit', sans-serif;
            margin-top: 4px;
        }

        .vademecum-card {
            background: var(--surface-vademecum);
            border: 1px solid var(--border-vademecum);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
        }
        .news-title-link {
            font-family: 'Outfit', sans-serif;
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--text-dark);
            text-decoration: none;
            margin-top: 12px;
            margin-bottom: 10px;
            display: block;
        }
        .news-title-link:hover {
            color: var(--accent-gold);
        }
        .news-summary-text {
            color: #44403c;
            font-size: 0.98rem;
            line-height: 1.6;
        }
    </style>
    """, unsafe_allow_html=True)

# Header Principal Hero VADEMECUM HUB NEWS
today_date_str = datetime.now().strftime("%d/%m/%Y")
last_update_str = st.session_state["last_updated"]

st.markdown(f"""
<div class="vademecum-hero">
    <div>
        <div class="vademecum-eyebrow">VADEMECUM HUB • RADAR DE INTELIGENCIA ESTRATÉGICA & NEWSLETTER</div>
        <div class="vademecum-title">VADEMECUM HUB <span>NEWS</span></div>
        <div class="vademecum-subtitle">Inteligencia Global • Medios de IA • <b style="color: #ff6e40;">REDDIT</b> • <b style="color: #7983f5;">DISCORD</b> • <b style="color: #c9a227;">NEWSLETTER CLIENTES</b></div>
    </div>
    <div class="vademecum-dates-box">
        <div class="vademecum-date-item">
            <span class="vademecum-date-label">📅 Edición Diaria</span>
            <span class="vademecum-date-val">{today_date_str}</span>
        </div>
        <div style="width: 1px; background: rgba(201, 162, 39, 0.3); margin: 0 4px;"></div>
        <div class="vademecum-date-item">
            <span class="vademecum-date-label">⏱️ Sincronización</span>
            <span class="vademecum-date-val">{last_update_str}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

def load_and_sync_all_sources(force_sync: bool = False):
    enricher = AIEnricher()
    existing_news = []
    existing_reddit = []
    existing_discord = []
    
    try:
        existing_news = db.get_all_news()
        existing_reddit = db.get_all_reddit()
        existing_discord = db.get_all_discord()
    except Exception as e:
        print(f"[Vademecum] Error leyendo SQLite: {e}")

    if not existing_news or force_sync:
        try:
            if force_sync:
                db.clear_all_news()
            raw_news = fetch_live_news()
            enriched = [enricher.enrich_item(item) for item in raw_news]
            db.save_news_items(enriched)
            existing_news = db.get_all_news()
            st.session_state["last_updated"] = datetime.now().strftime("%H:%M:%S")
        except Exception as e_sync:
            from backend.scraper import SEED_NEWS
            existing_news = SEED_NEWS

    if not existing_reddit or force_sync:
        try:
            if force_sync:
                db.clear_all_reddit()
            raw_reddit = fetch_top_reddit_discussions()
            db.save_reddit_items(raw_reddit)
            existing_reddit = db.get_all_reddit()
        except Exception as e_red:
            from backend.reddit_scraper import SEED_REDDIT_DISCUSSIONS
            existing_reddit = SEED_REDDIT_DISCUSSIONS

    if not existing_discord or force_sync:
        try:
            if force_sync:
                db.clear_all_discord()
            raw_discord = fetch_discord_messages()
            db.save_discord_items(raw_discord)
            existing_discord = db.get_all_discord()
        except Exception as e_dc:
            from backend.discord_reader import SEED_DISCORD_MESSAGES
            existing_discord = SEED_DISCORD_MESSAGES
            
    return existing_news, existing_reddit, existing_discord, enricher

if st.sidebar.button("🔄 Sincronizar Radar Completo", use_container_width=True, type="primary"):
    with st.spinner("Rastreando portales de IA, Reddit y Discord..."):
        news_data, reddit_data, discord_data, enricher = load_and_sync_all_sources(force_sync=True)
        st.session_state["just_synced"] = True
        st.rerun()
else:
    news_data, reddit_data, discord_data, enricher = load_and_sync_all_sources(force_sync=False)

search_term = st.sidebar.text_input("🔍 Búsqueda global", placeholder="ej. r/LocalLLaMA, Discord, MCP, Blackwell, o3...")
sources = ["Todas"] + sorted(list(set(item["source"] for item in news_data if item.get("source"))))
selected_source = st.sidebar.selectbox("🌐 Fuente de noticias", sources)
categories = ["Todas", "ROBÓTICA & EMBODIED AI"] + [c for c in sorted(list(set(item["category"] for item in news_data if item.get("category")))) if c != "ROBÓTICA & EMBODIED AI"]
selected_category = st.sidebar.selectbox("🏷️ Categoría temática", categories)

st.sidebar.markdown("---")

# KPIs VADEMECUM HUB
col_k1, col_k2, col_k3, col_k4 = st.columns(4)
with col_k1:
    st.markdown(f"""
    <div class="vademecum-kpi-card">
        <div class="vademecum-kpi-label">Noticias Tech Hoy</div>
        <div class="vademecum-kpi-value">{len(news_data)}</div>
    </div>
    """, unsafe_allow_html=True)
with col_k2:
    st.markdown(f"""
    <div class="vademecum-kpi-card" style="border-color: rgba(255, 69, 0, 0.45);">
        <div class="vademecum-kpi-label" style="color: #ff6e40;">Debates Reddit AI 💬</div>
        <div class="vademecum-kpi-value" style="color: #ff6e40;">{len(reddit_data)}</div>
    </div>
    """, unsafe_allow_html=True)
with col_k3:
    st.markdown(f"""
    <div class="vademecum-kpi-card" style="border-color: rgba(88, 101, 242, 0.45);">
        <div class="vademecum-kpi-label" style="color: #7983f5;">Canales Discord 🎮</div>
        <div class="vademecum-kpi-value" style="color: #7983f5;">{len(discord_data)}</div>
    </div>
    """, unsafe_allow_html=True)
with col_k4:
    sim_subs = newsletter_service.get_subscribers()
    st.markdown(f"""
    <div class="vademecum-kpi-card" style="border-color: rgba(201, 162, 39, 0.6);">
        <div class="vademecum-kpi-label" style="color: #c9a227;">Clientes Supabase 👥</div>
        <div class="vademecum-kpi-value" style="color: #c9a227;">{len(sim_subs)}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Pestañas Principales
tab_feed, tab_reddit, tab_discord, tab_chat, tab_newsletter, tab_favorites = st.tabs([
    "📰 Radar Vademecum", 
    "💬 Pulso Reddit", 
    "🎮 Pulso Discord", 
    "🤖 Asistente Vademecum", 
    "🚀 Lanzador Newsletter (Clientes)",
    "⭐ Guardados"
])

# Renderizado de Tarjetas Seguras
def render_vademecum_card(item: dict, key_prefix: str = "feed"):
    is_robotics = item.get("category") == "ROBÓTICA & EMBODIED AI"
    card_class = "vademecum-card vademecum-card-robotics" if is_robotics else "vademecum-card"
    category_badge_class = "badge-robotics-category" if is_robotics else "badge-category"
    
    is_fav = item["id"] in st.session_state["favorites"]
    fav_icon = "⭐ Guardada" if is_fav else "☆ Guardar"

    safe_title = clean_for_html(item.get("title", "Sin título"))
    safe_summary = clean_for_html(item.get("summary", ""))
    safe_source = clean_for_html(item.get("source", "Fuente"))
    safe_category = clean_for_html(item.get("category", "IA"))
    safe_badge = clean_for_html(item.get("sentiment_badge", "🚀 Innovación"))
    safe_url = html.escape(item.get("url", "#"))
    safe_date = html.escape(item.get("date", today_date_str))

    c_card, c_action = st.columns([0.88, 0.12])
    with c_card:
        action_btn_style = "text-decoration: none; font-weight: 700; color: #c9a227; font-size: 0.88rem; background: rgba(201, 162, 39, 0.12); padding: 6px 14px; border-radius: 8px; border: 1px solid rgba(201, 162, 39, 0.35);" if is_dark else "text-decoration: none; font-weight: 700; color: #b08a1c; font-size: 0.88rem; background: #fdfaf2; padding: 6px 14px; border-radius: 8px; border: 1px solid #d4af37;"
        st.markdown(f"""
        <div class="{card_class}">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span class="badge-source">🌐 {safe_source}</span>
                    <span class="{category_badge_class}">⚡ {safe_category}</span>
                    <span class="badge-category">{safe_badge}</span>
                </div>
                <div style="font-size: 0.82rem; color: #a8a29e; font-weight: 600; font-family: 'IBM Plex Mono', monospace;">
                    📅 {safe_date}
                </div>
            </div>
            <a href="{safe_url}" target="_blank" class="news-title-link">{safe_title}</a>
            <div class="news-summary-text">{safe_summary}</div>
            <div style="margin-top: 16px;">
                <a href="{safe_url}" target="_blank" style="{action_btn_style}">🔗 Leer Artículo Original ↗</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c_action:
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        btn_key = f"vademecum_fav_{key_prefix}_{item['id']}"
        if st.button(fav_icon, key=btn_key, use_container_width=True):
            if is_fav:
                db.remove_favorite(item["id"])
                st.session_state["favorites"].remove(item["id"])
                st.toast("Artículo eliminado de guardados", icon="🗑️")
            else:
                db.add_favorite(item["id"])
                st.session_state["favorites"].append(item["id"])
                st.toast("Artículo guardado", icon="⭐")
            st.rerun()

def render_reddit_card(item: dict, key_prefix: str = "reddit"):
    card_class = "vademecum-card"
    is_fav = item["id"] in st.session_state["favorites"]
    fav_icon = "⭐ Guardado" if is_fav else "☆ Guardar"
    
    safe_title = clean_for_html(item.get("title", "Sin título"))
    safe_summary = clean_for_html(item.get("summary", ""))
    safe_sub = clean_for_html(item.get("subreddit", "r/AI"))
    safe_author = clean_for_html(item.get("author", "u/anon"))
    safe_badge = clean_for_html(item.get("sentiment_badge", "🔥 Viral"))
    safe_url = html.escape(item.get("url", "#"))
    safe_date = html.escape(item.get("date", today_date_str))

    c_card, c_action = st.columns([0.88, 0.12])
    with c_card:
        action_btn_style = "text-decoration: none; font-weight: 700; color: #ff6e40; font-size: 0.88rem; background: rgba(255, 69, 0, 0.12); padding: 6px 14px; border-radius: 8px; border: 1px solid rgba(255, 69, 0, 0.4);" if is_dark else "text-decoration: none; font-weight: 700; color: #ea580c; font-size: 0.88rem; background: #fff7ed; padding: 6px 14px; border-radius: 8px; border: 1px solid #fed7aa;"
        st.markdown(f"""
        <div class="{card_class}">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span class="badge-reddit">🟠 {safe_sub}</span>
                    <span class="badge-category">{safe_badge}</span>
                    <span style="font-size: 0.8rem; color: #a8a29e; font-weight: 600;">👤 {safe_author}</span>
                </div>
                <div style="font-size: 0.82rem; color: #a8a29e; font-weight: 600; font-family: 'IBM Plex Mono', monospace;">
                    📅 {safe_date}
                </div>
            </div>
            <a href="{safe_url}" target="_blank" class="news-title-link">{safe_title}</a>
            <div class="news-summary-text">{safe_summary}</div>
            <div style="margin-top: 16px;">
                <a href="{safe_url}" target="_blank" style="{action_btn_style}">💬 Ver Debate en Reddit ↗</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c_action:
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        btn_key = f"reddit_fav_{key_prefix}_{item['id']}"
        if st.button(fav_icon, key=btn_key, use_container_width=True):
            if is_fav:
                db.remove_favorite(item["id"])
                st.session_state["favorites"].remove(item["id"])
                st.toast("Debate eliminado de guardados", icon="🗑️")
            else:
                db.add_favorite(item["id"])
                st.session_state["favorites"].append(item["id"])
                st.toast("Debate guardado", icon="⭐")
            st.rerun()

def render_discord_card(item: dict, key_prefix: str = "discord"):
    card_class = "vademecum-card"
    is_fav = item["id"] in st.session_state["favorites"]
    fav_icon = "⭐ Guardado" if is_fav else "☆ Guardar"
    
    safe_server = clean_for_html(item.get("server_name", "Servidor"))
    safe_channel = clean_for_html(item.get("channel_name", "#general"))
    safe_author = clean_for_html(item.get("author", "Miembro"))
    safe_badge = clean_for_html(item.get("sentiment_badge", "💬 Comunidad"))
    safe_summary = clean_for_html(item.get("summary", ""))
    safe_url = html.escape(item.get("url", "#"))
    safe_date = html.escape(item.get("date", today_date_str))

    c_card, c_action = st.columns([0.88, 0.12])
    with c_card:
        action_btn_style = "text-decoration: none; font-weight: 700; color: #7983f5; font-size: 0.88rem; background: rgba(88, 101, 242, 0.12); padding: 6px 14px; border-radius: 8px; border: 1px solid rgba(88, 101, 242, 0.4);" if is_dark else "text-decoration: none; font-weight: 700; color: #4f46e5; font-size: 0.88rem; background: #eef2ff; padding: 6px 14px; border-radius: 8px; border: 1px solid #c7d2fe;"
        st.markdown(f"""
        <div class="{card_class}">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span class="badge-discord">🎮 {safe_server} • {safe_channel}</span>
                    <span class="badge-category">{safe_badge}</span>
                    <span style="font-size: 0.8rem; color: #a8a29e; font-weight: 600;">👤 {safe_author}</span>
                </div>
                <div style="font-size: 0.82rem; color: #a8a29e; font-weight: 600; font-family: 'IBM Plex Mono', monospace;">
                    📅 {safe_date}
                </div>
            </div>
            <div style="margin-top: 12px; margin-bottom: 8px; font-family: 'Outfit', sans-serif; font-size: 1.15rem; font-weight: 700; color: var(--text-ivory);">
                💬 Discusión en {safe_channel}
            </div>
            <div class="news-summary-text">{safe_summary}</div>
            <div style="margin-top: 16px;">
                <a href="{safe_url}" target="_blank" style="{action_btn_style}">🎮 Abrir Mensaje en Discord ↗</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c_action:
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        btn_key = f"discord_fav_{key_prefix}_{item['id']}"
        if st.button(fav_icon, key=btn_key, use_container_width=True):
            if is_fav:
                db.remove_favorite(item["id"])
                st.session_state["favorites"].remove(item["id"])
                st.toast("Mensaje eliminado de guardados", icon="🗑️")
            else:
                db.add_favorite(item["id"])
                st.session_state["favorites"].append(item["id"])
                st.toast("Mensaje guardado", icon="⭐")
            st.rerun()

# PESTAÑA 1: RADAR NOTICIAS
with tab_feed:
    st.markdown(f"#### 📡 **{len(news_data)}** novedades tecnológicas en el Radar")
    for item in news_data:
        render_vademecum_card(item, key_prefix="main_feed")

# PESTAÑA 2: PULSO REDDIT
with tab_reddit:
    st.markdown("### 💬 Pulso de la Comunidad de IA en Reddit")
    for r_item in reddit_data:
        render_reddit_card(r_item, key_prefix="reddit_feed")

# PESTAÑA 3: PULSO DISCORD
with tab_discord:
    st.markdown("### 🎮 Canales de Discord de Servidores IA")
    for dc_item in discord_data:
        render_discord_card(dc_item, key_prefix="discord_feed")

# PESTAÑA 4: ASISTENTE VADEMECUM
with tab_chat:
    st.markdown("### 🤖 Asistente Estratégico Vademecum Hub")
    user_query = st.text_input("💬 Consulta estratégica, técnica o comunitaria:", placeholder="Ej. ¿Qué opinan en Reddit sobre los nuevos modelos abiertos?", key="vad_rag_input")
    if st.button("Consultar Asistente Vademecum", type="primary", key="vad_btn_send"):
        if user_query.strip():
            st.session_state["chat_history"].append({"role": "user", "text": user_query})
            with st.spinner("Analizando con Gemini AI..."):
                combined_context = news_data + reddit_data + discord_data
                ans = enricher.ask_feed(user_query, combined_context)
                st.session_state["chat_history"].append({"role": "assistant", "text": ans})
                st.rerun()
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.markdown(f"**👤 Consultor:** {msg['text']}")
        else:
            st.markdown(msg['text'])
            st.markdown("---")

# PESTAÑA 5: LANZADOR DE NEWSLETTER A CLIENTES
with tab_newsletter:
    st.markdown("### 🚀 Lanzador de Newsletter para Clientes (Supabase + Resend)")
    st.markdown("Compila el radar de inteligencia tecnológica y despáchalo a tu base de datos de clientes con **un solo clic**.")

    has_resend = bool(newsletter_service.resend_api_key)
    
    col_mode_sel, col_mode_info = st.columns([0.45, 0.55])
    with col_mode_sel:
        opciones_modo = ["🧪 Modo Simulador (Mock seguro)", "🚀 En Vivo con Resend API"] if has_resend else ["🧪 Modo Simulador (Mock seguro)"]
        modo_seleccionado = st.radio(
            "Modo de Operación:",
            opciones_modo,
            index=1 if has_resend else 0,
            horizontal=True,
            key="nl_operational_mode"
        )
    is_sim = "Simulador" in modo_seleccionado
    
    with col_mode_info:
        if not is_sim:
            st.markdown("""
            <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid #10b981; border-radius: 10px; padding: 10px 16px;">
                <div style="font-size: 0.78rem; font-weight: 800; color: #10b981; text-transform: uppercase;">🟢 RESEND API EN VIVO ACTIVA</div>
                <div style="font-size: 0.85rem; color: #d6d0c4; margin-top: 2px;">Los correos se enviarán realmente a través de los servidores de Resend.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: rgba(245, 158, 11, 0.12); border: 1px solid #f59e0b; border-radius: 10px; padding: 10px 16px;">
                <div style="font-size: 0.78rem; font-weight: 800; color: #f59e0b; text-transform: uppercase;">🟡 MODO SIMULADOR SEGURO</div>
                <div style="font-size: 0.85rem; color: #d6d0c4; margin-top: 2px;">Simulación de despacho con estadísticas sin consumir cuota real de envíos.</div>
            </div>
            """, unsafe_allow_html=True)
    
    # 1. Audiencia
    st.markdown("#### 1. Audiencia en Supabase (public.leads)")
    col_seg, col_count = st.columns([0.7, 0.3])
    with col_seg:
        segmento = st.selectbox("Segmento de Clientes", ["Todos", "Consultoria", "Formacion", "Apps"], key="nl_seg_sel")
    
    recipients = newsletter_service.get_subscribers(tipo_filtro=segmento)
    with col_count:
        st.metric(label="Clientes Seleccionados", value=f"{len(recipients)} destinatarios")
        
    with st.expander(f"👥 Ver lista de {len(recipients)} clientes listos en Supabase"):
        st.dataframe(pd.DataFrame(recipients)[["nombre", "email", "empresa", "tipo"]], use_container_width=True)

    st.markdown("---")
    
    # 2. Contenido y Asunto
    st.markdown("#### 2. Redacción y Asunto del Correo")
    default_subject = f"⚡ VADEMECUM HUB NEWS • Radar de IA & Robótica ({datetime.now().strftime('%d/%m/%Y')})"
    email_subject = st.text_input("Asunto de la Newsletter:", value=default_subject, key="nl_subject_input")
    
    if "newsletter_markdown" not in st.session_state:
        # Generar contenido inicial a partir del briefing
        st.session_state["newsletter_markdown"] = enricher.generate_daily_digest(news_data)
        if reddit_data:
            st.session_state["newsletter_markdown"] += "\n## 💬 PULSO DE LA COMUNIDAD (REDDIT HIGHLIGHTS)\n"
            for r in reddit_data[:2]:
                st.session_state["newsletter_markdown"] += f"• **{r['title']}** ({r['subreddit']})\n  {r['summary']}\n\n"
        if discord_data:
            st.session_state["newsletter_markdown"] += "\n## 🎮 ANUNCIOS EN DISCORD DE IA\n"
            for d in discord_data[:2]:
                st.session_state["newsletter_markdown"] += f"• **{d['server_name']}** ({d['channel_name']})\n  {d['summary']}\n\n"
                
    email_content_md = st.text_area("Cuerpo del Informe (Markdown editable):", value=st.session_state["newsletter_markdown"], height=200, key="nl_editor_md")
    
    # Generar versión HTML con la plantilla corporativa Vademecum
    html_email = newsletter_service.generate_html_email(email_content_md, email_subject)
    
    with st.expander("👁️ Previsualizar Email HTML (Diseño oficial Vademecum)"):
        st.components.v1.html(html_email, height=550, scrolling=True)
        
    st.markdown("---")
    
    # 3. Lanzador de Envíos
    st.markdown("#### 3. Acciones de Envío")
    col_test, col_send = st.columns([0.45, 0.55])
    
    default_sender = newsletter_service.sender_email
    sender_from = st.text_input("Dirección remitente (From):", value=default_sender, key="nl_sender_from_input", help="En cuentas nuevas de Resend sin dominio propio verificado, usa 'onboarding@resend.dev' para enviar a tu email registrado.")
    
    col_test, col_send = st.columns([0.45, 0.55])
    
    with col_test:
        st.markdown("**🧪 Envío de Prueba:**")
        partner_emails = st.text_input("Emails tuyo y de tu socio (coma):", value="martin@vademecumhub.com, socio@vademecumhub.com", key="nl_test_emails")
        if st.button("Enviar Prueba a Socios", use_container_width=True, key="btn_send_test"):
            test_recipients = [{"email": e.strip(), "nombre": "Socio"} for e in partner_emails.split(",") if e.strip()]
            with st.spinner("Despachando prueba..."):
                time.sleep(0.5)
                res = newsletter_service.send_newsletter(test_recipients, f"[PRUEBA] {email_subject}", html_email, is_simulation=is_sim, sender_email=sender_from)
                if res['sent'] > 0:
                    st.success(f"✅ ¡Prueba despachada a {res['sent']} destinatario(s)! ({res['mode']})")
                if res['failed'] > 0:
                    st.error(f"⚠️ {res['failed']} envío(s) no completados en Resend: {', '.join(res['errors'])}")
                
    with col_send:
        st.markdown("**🚀 Disparo Masivo a Clientes:**")
        st.markdown(f"Se enviará a **{len(recipients)} clientes**.")
        if st.button("🚀 ENVIAR NEWSLETTER A CLIENTES (1 CLIC)", type="primary", use_container_width=True, key="btn_send_all_clients"):
            progress_bar = st.progress(0, text="Iniciando conexión con el motor de envíos...")
            for i, r in enumerate(recipients):
                time.sleep(0.1)
                progress_bar.progress((i + 1) / len(recipients), text=f"Despachando a {r['email']} ({r.get('empresa', 'Cliente')})...")
                
            res = newsletter_service.send_newsletter(recipients, email_subject, html_email, is_simulation=is_sim, sender_email=sender_from)
            progress_bar.empty()
            
            if res['sent'] > 0:
                st.balloons()
                st.success(f"""
                🎉 **¡Newsletter despachada exitosamente!**
                * **Destinatarios entregados:** {res['sent']} / {res['total']}
                * **Modo:** {res['mode']}
                * **Hora de registro:** {res['timestamp']}
                """)
            if res['failed'] > 0:
                st.warning(f"⚠️ {res['failed']} envíos devueltos por Resend: {res['errors']}")
            
            st.session_state["campaign_history"].append({
                "fecha": res['timestamp'],
                "asunto": email_subject,
                "destinatarios": res['sent'],
                "modo": res['mode']
            })

    if st.session_state["campaign_history"]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 📜 Histórico de Campañas Enviadas en esta Sesión:")
        st.dataframe(pd.DataFrame(st.session_state["campaign_history"]), use_container_width=True)

# PESTAÑA 6: GUARDADOS
with tab_favorites:
    st.markdown("### ⭐ Elementos Guardados en Vademecum")
    fav_ids = set(st.session_state["favorites"])
    fav_news = [item for item in news_data if item["id"] in fav_ids]
    fav_reddit = [item for item in reddit_data if item["id"] in fav_ids]
    fav_discord = [item for item in discord_data if item["id"] in fav_ids]
    
    total_favs = len(fav_news) + len(fav_reddit) + len(fav_discord)
    if total_favs == 0:
        st.info("Aún no tienes elementos guardados.")
    else:
        st.markdown(f"Tienes **{total_favs} elementos** guardados:")
        if fav_news:
            st.markdown("##### 📰 Noticias Guardadas:")
            for item in fav_news:
                render_vademecum_card(item, key_prefix="fav_news")
        if fav_reddit:
            st.markdown("##### 💬 Debates de Reddit Guardados:")
            for item in fav_reddit:
                render_reddit_card(item, key_prefix="fav_reddit")
        if fav_discord:
            st.markdown("##### 🎮 Mensajes de Discord Guardados:")
            for item in fav_discord:
                render_discord_card(item, key_prefix="fav_discord")

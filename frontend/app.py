import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import base64
import html
import re
from dotenv import load_dotenv

# Cargar variables del entorno desde .env
load_dotenv()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.scraper import fetch_live_news
from backend.reddit_scraper import fetch_top_reddit_discussions
from backend.discord_reader import fetch_discord_messages
from backend.ai_enricher import AIEnricher
from backend.db_manager import DatabaseManager

st.set_page_config(
    page_title="VADEMECUM HUB NEWS • Radar de IA, Robótica, Reddit & Discord",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar Base de Datos SQLite
db = DatabaseManager()

# Inicializar estado en sesión
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

st.session_state["favorites"] = db.get_favorites()

# Helper de Sanitización Total contra fugas de HTML/Markdown
def clean_for_html(text: str) -> str:
    """Elimina residuos de etiquetas rotas y convierte texto en HTML seguro y limpio."""
    if not text:
        return ""
    # Quitar etiquetas html crudas o rotas como <a href... o >a ref...
    text = re.sub(r'</?[a-zA-Z][^>]*>', '', text)
    text = re.sub(r'>a\s+ref[^<]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'a\s+href[^<]*', '', text, flags=re.IGNORECASE)
    # Quitar sintaxis markdown de enlace [texto](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Escapar caracteres especiales
    text = html.escape(text)
    # Restaurar viñetas y negritas seguras
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = text.replace('\n', '<br>')
    return text

# Cargar logo de Vademecum en base64 para uso inline
LOGO_PATH = os.path.join(CURRENT_DIR, "assets", "logo.jpg")
logo_b64 = ""
if os.path.exists(LOGO_PATH):
    try:
        with open(LOGO_PATH, "rb") as img_f:
            logo_b64 = base64.b64encode(img_f.read()).decode("utf-8")
    except Exception:
        logo_b64 = ""

# --- SIDEBAR: PANEL VADEMECUM HUB ---
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

# Selector de Tema
theme_mode = st.sidebar.radio(
    "🎨 Estilo Visual",
    ["🌙 Vademecum Dark", "☀️ Vademecum Light"],
    index=0 if st.session_state["theme"] == "dark" else 1,
    horizontal=True
)
st.session_state["theme"] = "dark" if "Dark" in theme_mode else "light"
is_dark = st.session_state["theme"] == "dark"

# SISTEMA DE DISEÑO VADEMECUM HUB (Paleta oficial: #0e0d0c, #f4efe6, #c9a227, #2e2a24, #161411)
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
            --accent-discord: #5865F2;
            --accent-reddit: #ff4500;
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
        
        .vademecum-card-robotics {
            background: linear-gradient(135deg, rgba(22, 20, 17, 0.95) 0%, rgba(35, 29, 20, 0.9) 100%) !important;
            border: 1px solid rgba(201, 162, 39, 0.6) !important;
            box-shadow: 0 4px 24px rgba(201, 162, 39, 0.12) !important;
        }

        .vademecum-card-reddit {
            background: linear-gradient(135deg, rgba(26, 20, 15, 0.92) 0%, rgba(22, 20, 17, 0.95) 100%) !important;
            border: 1px solid rgba(255, 69, 0, 0.35) !important;
        }
        .vademecum-card-reddit:hover {
            border-color: #ff4500 !important;
            box-shadow: 0 10px 32px rgba(255, 69, 0, 0.25) !important;
        }

        .vademecum-card-discord {
            background: linear-gradient(135deg, rgba(20, 20, 32, 0.92) 0%, rgba(22, 20, 17, 0.95) 100%) !important;
            border: 1px solid rgba(88, 101, 242, 0.35) !important;
        }
        .vademecum-card-discord:hover {
            border-color: #5865F2 !important;
            box-shadow: 0 10px 32px rgba(88, 101, 242, 0.25) !important;
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
            box-shadow: 0 2px 10px rgba(201, 162, 39, 0.35) !important;
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
    # MODO VADEMECUM LIGHT
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

        .vademecum-dates-box {
            display: flex;
            background: #ffffff;
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
            color: var(--text-dark);
            font-family: 'IBM Plex Mono', monospace;
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
            transition: all 0.25s ease;
        }
        .vademecum-card:hover {
            transform: translateY(-3px);
            border-color: var(--accent-gold);
            box-shadow: 0 8px 24px rgba(176, 138, 28, 0.12);
        }
        
        .vademecum-card-reddit {
            background: #ffffff !important;
            border: 1px solid #fed7aa !important;
        }
        .vademecum-card-discord {
            background: #ffffff !important;
            border: 1px solid #c7d2fe !important;
        }

        .badge-source {
            background: #f5f2eb;
            border: 1px solid var(--border-vademecum);
            color: #44403c;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 600;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-reddit {
            background: #fff7ed;
            border: 1px solid #ffedd5;
            color: #ea580c;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 800;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-discord {
            background: #eef2ff;
            border: 1px solid #e0e7ff;
            color: #4f46e5;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 800;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-category {
            background: #fbf7ee;
            border: 1px solid #d4af37;
            color: var(--accent-gold);
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
            margin-right: 8px;
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
        <div class="vademecum-eyebrow">VADEMECUM HUB • RADAR DE INTELIGENCIA ESTRATÉGICA & COMUNIDADES</div>
        <div class="vademecum-title">VADEMECUM HUB <span>NEWS</span></div>
        <div class="vademecum-subtitle">Inteligencia Global • Medios de IA • <b style="color: #ff6e40;">REDDIT</b> • <b style="color: #7983f5;">DISCORD</b> • <b style="color: #c9a227;">ROBÓTICA</b></div>
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

if st.session_state["just_synced"]:
    st.toast("⚡ Vademecum Hub News, Reddit & Discord resincronizados", icon="🚀")
    st.success("Radar resincronizado con éxito desde fuentes globales, Reddit y Discord.")
    st.session_state["just_synced"] = False

# Cargar y sincronizar datos globales
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

# Botón de Sincronización en Sidebar
if st.sidebar.button("🔄 Sincronizar Radar Completo", use_container_width=True, type="primary"):
    with st.spinner("Rastreando portales de IA, hilos en Reddit y canales de Discord..."):
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

sentiment_options = ["Todos", "Innovación", "Oportunidad", "Alerta", "Tendencia", "Actualización"]
selected_sentiment = st.sidebar.selectbox("📊 Impacto / Sentimiento", sentiment_options)

st.sidebar.markdown("---")

# Configuración Rápida de Discord en Sidebar
with st.sidebar.expander("⚙️ Conexión Canales Discord"):
    st.markdown("<small>Introduce tu token y los IDs de los canales a los que perteneces (separados por coma):</small>", unsafe_allow_html=True)
    dc_tok_input = st.text_input("Token Discord:", value=os.environ.get("DISCORD_USER_TOKEN", ""), type="password", key="side_dc_tok")
    dc_ch_input = st.text_input("IDs de Canales:", value=os.environ.get("DISCORD_CHANNEL_IDS", ""), placeholder="123456789,987654321", key="side_dc_ch")
    if st.button("Guardar y Sincronizar Discord", key="btn_save_dc"):
        ch_list = [c.strip() for c in dc_ch_input.split(",") if c.strip()]
        with st.spinner("Conectando con Discord..."):
            new_dc = fetch_discord_messages(token=dc_tok_input, channel_ids=ch_list)
            db.clear_all_discord()
            db.save_discord_items(new_dc)
            st.toast("Canales Discord sincronizados con éxito", icon="🎮")
            st.rerun()

ai_status_color = "#10b981" if enricher.client else "#c9a227"
ai_status_text = "🟢 Gemini AI Activo" if enricher.client else "🟡 Motor Heurístico Vademecum"

sidebar_card_bg = "#161411" if is_dark else "#fdfbf7"
sidebar_card_border = "#2e2a24" if is_dark else "#e7e2d8"
sidebar_title_color = "#f4efe6" if is_dark else "#1c1917"

st.sidebar.markdown(f"""
<div style="background: {sidebar_card_bg}; border: 1px solid {sidebar_card_border}; border-radius: 10px; padding: 14px; margin-bottom: 15px;">
    <div style="font-size: 0.76rem; color: #c9a227; font-weight: 700; text-transform: uppercase;">🤖 Inteligencia Artificial</div>
    <div style="font-size: 0.9rem; color: {ai_status_color}; font-weight: 700; margin-top: 4px;">{ai_status_text}</div>
    <div style="font-size: 0.80rem; color: #a8a29e; margin-top: 8px;">💾 {len(news_data)} noticias • {len(reddit_data)} Reddit • {len(discord_data)} Discord</div>
</div>
""", unsafe_allow_html=True)

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
    fav_count = len(st.session_state["favorites"])
    st.markdown(f"""
    <div class="vademecum-kpi-card">
        <div class="vademecum-kpi-label">Guardados ⭐</div>
        <div class="vademecum-kpi-value" style="color: #e5be38;">{fav_count}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Tendencias Rápidas
st.markdown("##### 🔥 Temáticas de Vanguardia en Vademecum:")
tag_cols = st.columns(6)
all_tags = ["Todos", "#Robótica", "#LLMs", "#LocalLLM", "#HardwareNVIDIA", "#MCP"]
for i, tag in enumerate(all_tags):
    if tag_cols[i].button(tag, key=f"btn_vademecum_tag_{i}", use_container_width=True):
        st.session_state["selected_tag"] = tag

# Pestañas Principales
tab_feed, tab_reddit, tab_discord, tab_chat, tab_favorites, tab_digest = st.tabs([
    "📰 Radar Vademecum", 
    "💬 Pulso Reddit", 
    "🎮 Pulso Discord", 
    "🤖 Asistente Vademecum", 
    "⭐ Elementos Guardados", 
    "📝 Daily Briefing"
])

# Renderizado de Tarjeta de Noticias 100% LIMPIA
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
    
    hashtags_list = item.get("hashtags", [])
    safe_tags = " ".join([clean_for_html(t) for t in hashtags_list]) if isinstance(hashtags_list, list) else ""

    c_card, c_action = st.columns([0.88, 0.12])
    with c_card:
        action_btn_style = "text-decoration: none; font-weight: 700; color: #c9a227; font-size: 0.88rem; background: rgba(201, 162, 39, 0.12); padding: 6px 14px; border-radius: 8px; border: 1px solid rgba(201, 162, 39, 0.35);" if is_dark else "text-decoration: none; font-weight: 700; color: #b08a1c; font-size: 0.88rem; background: #fdfaf2; padding: 6px 14px; border-radius: 8px; border: 1px solid #d4af37;"
        tag_color = "#c9a227" if is_dark else "#b08a1c"
        date_color = "#a8a29e" if is_dark else "#78716c"
        
        st.markdown(f"""
        <div class="{card_class}">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span class="badge-source">🌐 {safe_source}</span>
                    <span class="{category_badge_class}">⚡ {safe_category}</span>
                    <span class="badge-category">{safe_badge}</span>
                </div>
                <div style="font-size: 0.82rem; color: {date_color}; font-weight: 600; font-family: 'IBM Plex Mono', monospace;">
                    📅 {safe_date}
                </div>
            </div>
            <a href="{safe_url}" target="_blank" class="news-title-link">
                {safe_title}
            </a>
            <div class="news-summary-text">
                {safe_summary}
            </div>
            <div style="margin-top: 16px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div style="font-size: 0.82rem; color: {tag_color}; font-weight: 700;">
                    {safe_tags}
                </div>
                <a href="{safe_url}" target="_blank" style="{action_btn_style}">
                    🔗 Leer Artículo Original ↗
                </a>
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
                st.toast("Artículo guardado en Vademecum", icon="⭐")
            st.rerun()

# Renderizado de Tarjeta de Reddit 100% LIMPIA
def render_reddit_card(item: dict, key_prefix: str = "reddit"):
    card_class = "vademecum-card vademecum-card-reddit"
    is_fav = item["id"] in st.session_state["favorites"]
    fav_icon = "⭐ Guardado" if is_fav else "☆ Guardar"
    
    safe_title = clean_for_html(item.get("title", "Sin título"))
    safe_summary = clean_for_html(item.get("summary", ""))
    safe_sub = clean_for_html(item.get("subreddit", "r/AI"))
    safe_author = clean_for_html(item.get("author", "u/anon"))
    safe_badge = clean_for_html(item.get("sentiment_badge", "🔥 Viral"))
    safe_url = html.escape(item.get("url", "#"))
    safe_date = html.escape(item.get("date", today_date_str))
    
    hashtags_list = item.get("hashtags", [])
    safe_tags = " ".join([clean_for_html(t) for t in hashtags_list]) if isinstance(hashtags_list, list) else ""

    c_card, c_action = st.columns([0.88, 0.12])
    with c_card:
        action_btn_style = "text-decoration: none; font-weight: 700; color: #ff6e40; font-size: 0.88rem; background: rgba(255, 69, 0, 0.12); padding: 6px 14px; border-radius: 8px; border: 1px solid rgba(255, 69, 0, 0.4);" if is_dark else "text-decoration: none; font-weight: 700; color: #ea580c; font-size: 0.88rem; background: #fff7ed; padding: 6px 14px; border-radius: 8px; border: 1px solid #fed7aa;"
        tag_color = "#ff6e40" if is_dark else "#ea580c"
        date_color = "#a8a29e" if is_dark else "#78716c"
        
        st.markdown(f"""
        <div class="{card_class}">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span class="badge-reddit">🟠 {safe_sub}</span>
                    <span class="badge-category">{safe_badge}</span>
                    <span style="font-size: 0.8rem; color: #a8a29e; font-weight: 600;">👤 {safe_author}</span>
                </div>
                <div style="font-size: 0.82rem; color: {date_color}; font-weight: 600; font-family: 'IBM Plex Mono', monospace;">
                    📅 {safe_date}
                </div>
            </div>
            <a href="{safe_url}" target="_blank" class="news-title-link">
                {safe_title}
            </a>
            <div class="news-summary-text">
                {safe_summary}
            </div>
            <div style="margin-top: 16px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div style="font-size: 0.82rem; color: {tag_color}; font-weight: 700;">
                    {safe_tags}
                </div>
                <a href="{safe_url}" target="_blank" style="{action_btn_style}">
                    💬 Ver Conversación en Reddit ↗
                </a>
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
                st.toast("Debate de Reddit guardado", icon="⭐")
            st.rerun()

# Renderizado de Tarjeta de Discord 100% LIMPIA
def render_discord_card(item: dict, key_prefix: str = "discord"):
    card_class = "vademecum-card vademecum-card-discord"
    is_fav = item["id"] in st.session_state["favorites"]
    fav_icon = "⭐ Guardado" if is_fav else "☆ Guardar"
    
    safe_server = clean_for_html(item.get("server_name", "Servidor"))
    safe_channel = clean_for_html(item.get("channel_name", "#general"))
    safe_author = clean_for_html(item.get("author", "Miembro"))
    safe_badge = clean_for_html(item.get("sentiment_badge", "💬 Comunidad"))
    safe_summary = clean_for_html(item.get("summary", ""))
    safe_url = html.escape(item.get("url", "#"))
    safe_date = html.escape(item.get("date", today_date_str))
    
    hashtags_list = item.get("hashtags", [])
    safe_tags = " ".join([clean_for_html(t) for t in hashtags_list]) if isinstance(hashtags_list, list) else ""

    c_card, c_action = st.columns([0.88, 0.12])
    with c_card:
        action_btn_style = "text-decoration: none; font-weight: 700; color: #7983f5; font-size: 0.88rem; background: rgba(88, 101, 242, 0.12); padding: 6px 14px; border-radius: 8px; border: 1px solid rgba(88, 101, 242, 0.4);" if is_dark else "text-decoration: none; font-weight: 700; color: #4f46e5; font-size: 0.88rem; background: #eef2ff; padding: 6px 14px; border-radius: 8px; border: 1px solid #c7d2fe;"
        tag_color = "#7983f5" if is_dark else "#4f46e5"
        date_color = "#a8a29e" if is_dark else "#78716c"
        
        st.markdown(f"""
        <div class="{card_class}">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span class="badge-discord">🎮 {safe_server} • {safe_channel}</span>
                    <span class="badge-category">{safe_badge}</span>
                    <span style="font-size: 0.8rem; color: #a8a29e; font-weight: 600;">👤 {safe_author}</span>
                </div>
                <div style="font-size: 0.82rem; color: {date_color}; font-weight: 600; font-family: 'IBM Plex Mono', monospace;">
                    📅 {safe_date}
                </div>
            </div>
            <div style="margin-top: 12px; margin-bottom: 10px; font-family: 'Outfit', sans-serif; font-size: 1.15rem; font-weight: 700; color: var(--text-ivory);">
                💬 Discusión en {safe_channel}
            </div>
            <div class="news-summary-text">
                {safe_summary}
            </div>
            <div style="margin-top: 16px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div style="font-size: 0.82rem; color: {tag_color}; font-weight: 700;">
                    {safe_tags}
                </div>
                <a href="{safe_url}" target="_blank" style="{action_btn_style}">
                    🎮 Abrir Mensaje en Discord ↗
                </a>
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
                st.toast("Mensaje de Discord guardado", icon="⭐")
            st.rerun()

# Filtrado de Noticias
filtered_news = news_data
if st.session_state["selected_tag"] != "Todos":
    tag_clean = st.session_state["selected_tag"]
    filtered_news = [item for item in filtered_news if tag_clean in item.get("hashtags", [])]

if search_term:
    search_lower = search_term.lower()
    filtered_news = [
        item for item in filtered_news 
        if search_lower in item.get("title", "").lower() 
        or search_lower in item.get("summary", "").lower()
        or search_lower in item.get("source", "").lower()
        or search_lower in item.get("category", "").lower()
        or any(search_lower in tag.lower() for tag in item.get("hashtags", []))
    ]

if selected_source != "Todas":
    filtered_news = [item for item in filtered_news if item.get("source") == selected_source]

if selected_category != "Todas":
    filtered_news = [item for item in filtered_news if item.get("category") == selected_category]

if selected_sentiment != "Todos":
    filtered_news = [item for item in filtered_news if item.get("sentiment") == selected_sentiment]

# PESTAÑA 1: RADAR NOTICIAS
with tab_feed:
    st.markdown(f"#### 📡 **{len(filtered_news)}** novedades tecnológicas en el Radar")
    if not filtered_news:
        st.info("No se han encontrado novedades que coincidan con los filtros seleccionados.")
    else:
        for item in filtered_news:
            render_vademecum_card(item, key_prefix="main_feed")

# PESTAÑA 2: PULSO REDDIT
with tab_reddit:
    st.markdown("### 💬 Pulso de la Comunidad de IA en Reddit")
    st.markdown("Discusiones más votadas en **r/LocalLLaMA, r/MachineLearning, r/singularity, r/robotics, r/OpenAI y r/ClaudeAI**.")
    
    reddit_subs = ["Todos", "r/LocalLLaMA", "r/OpenAI", "r/ClaudeAI", "r/singularity", "r/robotics", "r/MachineLearning"]
    col_sub_select, col_sub_badge = st.columns([0.6, 0.4])
    with col_sub_select:
        sel_sub = st.selectbox("Subreddit", reddit_subs, key="reddit_sub_selector")
    with col_sub_badge:
        sel_badge = st.selectbox("Tipo de Debate", ["Todos", "🔥 Viral", "🛠️ Técnico", "💡 Innovación", "⚠️ Crítica / Bug", "🦾 Robótica"], key="reddit_badge_selector")
        
    filtered_reddit = reddit_data
    if sel_sub != "Todos":
        filtered_reddit = [r for r in filtered_reddit if r.get("subreddit", "").lower() == sel_sub.lower()]
    if sel_badge != "Todos":
        filtered_reddit = [r for r in filtered_reddit if sel_badge in r.get("sentiment_badge", "")]
        
    if search_term:
        s_lower = search_term.lower()
        filtered_reddit = [
            r for r in filtered_reddit 
            if s_lower in r.get("title", "").lower() 
            or s_lower in r.get("summary", "").lower() 
            or s_lower in r.get("subreddit", "").lower()
            or any(s_lower in t.lower() for t in r.get("hashtags", []))
        ]
        
    st.markdown(f"Mostrando **{len(filtered_reddit)} debates activos:**")
    if not filtered_reddit:
        st.info("No hay hilos de Reddit que coincidan con los filtros seleccionados.")
    else:
        for r_item in filtered_reddit:
            render_reddit_card(r_item, key_prefix="reddit_feed")

# PESTAÑA 3: PULSO DISCORD
with tab_discord:
    st.markdown("### 🎮 Canales de Discord de Servidores IA")
    st.markdown("Monitorización de canales de anuncios, lanzamientos y debate en los servidores de los que eres miembro.")
    
    servers_list = ["Todos"] + sorted(list(set(d.get("server_name", "Servidor") for d in discord_data)))
    sel_server = st.selectbox("Servidor de Discord", servers_list, key="dc_server_sel")
    
    filtered_discord = discord_data
    if sel_server != "Todos":
        filtered_discord = [d for d in filtered_discord if d.get("server_name") == sel_server]
        
    if search_term:
        s_lower = search_term.lower()
        filtered_discord = [
            d for d in filtered_discord
            if s_lower in d.get("content", "").lower()
            or s_lower in d.get("summary", "").lower()
            or s_lower in d.get("server_name", "").lower()
            or s_lower in d.get("channel_name", "").lower()
        ]
        
    st.markdown(f"Mostrando **{len(filtered_discord)} mensajes y anuncios:**")
    if not filtered_discord:
        st.info("No hay mensajes de Discord disponibles para los filtros seleccionados.")
    else:
        for dc_item in filtered_discord:
            render_discord_card(dc_item, key_prefix="discord_feed")

# PESTAÑA 4: ASISTENTE VADEMECUM (CHAT RAG)
with tab_chat:
    st.markdown("### 🤖 Asistente Estratégico Vademecum Hub")
    st.markdown("Consulta y analiza de forma cruzada noticias de medios, debates en Reddit y anuncios en canales de Discord.")
    
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        if st.button("💬 ¿Qué se debate en Reddit sobre modelos de razonamiento y matemática?", use_container_width=True, key="vad_sug_red_1"):
            st.session_state["chat_history"].append({"role": "user", "text": "¿Qué se está diciendo en Reddit sobre modelos de razonamiento de OpenAI?"})
            with st.spinner("Analizando con Gemini AI..."):
                combined_context = news_data + reddit_data + discord_data
                ans = enricher.ask_feed("¿Qué se está diciendo en Reddit sobre modelos de razonamiento de OpenAI?", combined_context)
                st.session_state["chat_history"].append({"role": "assistant", "text": ans})
                st.rerun()
        if st.button("🎮 ¿Qué anuncios recientes hay en los canales de Discord de IA?", use_container_width=True, key="vad_sug_dc_1"):
            st.session_state["chat_history"].append({"role": "user", "text": "¿Cuáles son los anuncios y releases más recientes en los canales de Discord?"})
            with st.spinner("Analizando canales de Discord con Gemini AI..."):
                combined_context = news_data + reddit_data + discord_data
                ans = enricher.ask_feed("¿Cuáles son los anuncios y releases más recientes en los canales de Discord?", combined_context)
                st.session_state["chat_history"].append({"role": "assistant", "text": ans})
                st.rerun()
    with col_q2:
        if st.button("🛠️ ¿Cómo impacta Model Context Protocol (MCP) en arquitecturas de agentes?", use_container_width=True, key="vad_sug_3"):
            st.session_state["chat_history"].append({"role": "user", "text": "¿Cómo impacta Model Context Protocol (MCP) en arquitecturas de agentes?"})
            with st.spinner("Analizando con Gemini AI..."):
                ans = enricher.ask_feed("¿Cómo impacta Model Context Protocol (MCP) en arquitecturas de agentes?", news_data)
                st.session_state["chat_history"].append({"role": "assistant", "text": ans})
                st.rerun()
        if st.button("🦾 ¿Qué avances recientes hay en robots humanoides y manipulación?", use_container_width=True, key="vad_sug_4"):
            st.session_state["chat_history"].append({"role": "user", "text": "¿Qué avances recientes hay en robots humanoides y manipulación industrial?"})
            with st.spinner("Consultando fuentes con Gemini AI..."):
                ans = enricher.ask_feed("¿Qué avances recientes hay en robots humanoides y manipulación industrial?", news_data)
                st.session_state["chat_history"].append({"role": "assistant", "text": ans})
                st.rerun()

    st.markdown("---")
    
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.markdown(f"**👤 Consultor Vademecum:** {msg['text']}")
        else:
            st.markdown(msg['text'])
            st.markdown("---")
            
    user_query = st.text_input("💬 Consulta estratégica, técnica o comunitaria:", placeholder="Ej. ¿Qué opinan en Reddit y Discord sobre los nuevos modelos abiertos?", key="vad_rag_input")
    if st.button("Consultar Asistente Vademecum", type="primary", key="vad_btn_send"):
        if user_query.strip():
            st.session_state["chat_history"].append({"role": "user", "text": user_query})
            with st.spinner("Analizando fuentes combinadas..."):
                combined_context = news_data + reddit_data + discord_data
                ans = enricher.ask_feed(user_query, combined_context)
                st.session_state["chat_history"].append({"role": "assistant", "text": ans})
                st.rerun()

# PESTAÑA 5: MIS FAVORITOS
with tab_favorites:
    st.markdown("### ⭐ Elementos Guardados en Vademecum")
    fav_ids = set(st.session_state["favorites"])
    fav_news = [item for item in news_data if item["id"] in fav_ids]
    fav_reddit = [item for item in reddit_data if item["id"] in fav_ids]
    fav_discord = [item for item in discord_data if item["id"] in fav_ids]
    
    total_favs = len(fav_news) + len(fav_reddit) + len(fav_discord)
    if total_favs == 0:
        st.info("Aún no tienes elementos guardados. Pulsa en '☆ Guardar' en cualquier tarjeta para agregarlo a tu dossier.")
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

# PESTAÑA 6: MORNING BRIEFING
with tab_digest:
    st.markdown("### 📝 Vademecum Daily AI Briefing")
    st.markdown("Informe ejecutivo matinal combinando noticias de prensa tecnológica, pulso de Reddit y anuncios de Discord.")
    
    if st.button("⚡ Compilar Daily Briefing Completo", type="primary", key="vad_btn_gen_digest"):
        with st.spinner("Compilando análisis ejecutivo..."):
            digest_content = enricher.generate_daily_digest(news_data)
            if reddit_data:
                digest_content += "\n## 💬 PULSO DE LA COMUNIDAD (REDDIT HIGHLIGHTS)\n"
                for r in reddit_data[:3]:
                    digest_content += f"• **{r['title']}** ({r['subreddit']} por {r['author']})\n  {r['summary']}\n  🔗 [Ver hilo en Reddit]({r['url']})\n\n"
            if discord_data:
                digest_content += "\n## 🎮 ANUNCIOS Y PULSO EN DISCORD\n"
                for d in discord_data[:3]:
                    digest_content += f"• **{d['server_name']} ({d['channel_name']})** por {d['author']}\n  {d['summary']}\n\n"
            st.session_state["generated_digest"] = digest_content
            
    if "generated_digest" in st.session_state:
        st.markdown("---")
        st.download_button(
            label="📥 Descargar Vademecum Briefing (.md)",
            data=st.session_state["generated_digest"],
            file_name=f"vademecum_briefing_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            key="vad_btn_download_digest"
        )
        st.markdown(st.session_state["generated_digest"])

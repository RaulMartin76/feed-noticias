import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import base64
from dotenv import load_dotenv

# Cargar variables del entorno desde .env
load_dotenv()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.scraper import fetch_live_news
from backend.ai_enricher import AIEnricher
from backend.db_manager import DatabaseManager

st.set_page_config(
    page_title="VADEMECUM HUB NEWS • Radar de IA & Robótica",
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

# Selector de Tema (Vademecum Dark vs Parchment Light)
theme_mode = st.sidebar.radio(
    "🎨 Estilo Visual",
    ["🌙 Vademecum Dark", "☀️ Vademecum Light"],
    index=0 if st.session_state["theme"] == "dark" else 1,
    horizontal=True
)
st.session_state["theme"] = "dark" if "Dark" in theme_mode else "light"
is_dark = st.session_state["theme"] == "dark"

# SISTEMA DE DISEÑO VADEMECUM HUB (Inspirado en la paleta oficial: #0e0d0c, #f4efe6, #c9a227, #2e2a24, #161411)
if is_dark:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        :root {
            --bg-vademecum: #0e0d0c;
            --surface-vademecum: #161411;
            --card-vademecum: #181512;
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

        /* Ambient Hero Header Vademecum */
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
        .vademecum-date-item {
            display: flex;
            flex-direction: column;
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

        /* KPI Cards Vademecum */
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

        /* News Cards Vademecum */
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
        .vademecum-card-robotics:hover {
            border-color: var(--accent-gold-hover) !important;
            box-shadow: 0 10px 32px rgba(201, 162, 39, 0.25) !important;
        }

        /* Badges Vademecum */
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
        .badge-tone-innovation {
            background: rgba(47, 111, 106, 0.18);
            border: 1px solid rgba(47, 111, 106, 0.5);
            color: #4ade80;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-tone-alert {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(248, 113, 113, 0.35);
            color: #f87171;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-tone-trend {
            background: rgba(201, 162, 39, 0.15);
            border: 1px solid rgba(201, 162, 39, 0.4);
            color: #e5be38;
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
            white-space: pre-line;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    # MODO VADEMECUM LIGHT (Tech Parchment)
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
        
        .vademecum-card-robotics {
            background: linear-gradient(135deg, #fffdf8 0%, #ffffff 100%) !important;
            border: 1px solid #d4af37 !important;
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
        .badge-robotics-category {
            background: linear-gradient(135deg, #b08a1c 0%, #c9a227 100%) !important;
            color: #ffffff !important;
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
            white-space: pre-line;
        }
    </style>
    """, unsafe_allow_html=True)

# Header Principal Hero VADEMECUM HUB NEWS
today_date_str = datetime.now().strftime("%d/%m/%Y")
last_update_str = st.session_state["last_updated"]

st.markdown(f"""
<div class="vademecum-hero">
    <div>
        <div class="vademecum-eyebrow">VADEMECUM HUB • RADAR DE INTELIGENCIA ESTRATÉGICA</div>
        <div class="vademecum-title">VADEMECUM HUB <span>NEWS</span></div>
        <div class="vademecum-subtitle">Inteligencia Global en Tiempo Real para Consultoría de IA • Modelos • Hardware • <b style="color: #c9a227;">ROBÓTICA & EMBODIED AI</b></div>
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
    st.toast("⚡ Vademecum Hub News resincronizado con éxito desde fuentes globales", icon="🚀")
    st.success("Vademecum Hub News resincronizado con éxito desde fuentes globales de IA y Robótica.")
    st.session_state["just_synced"] = False

# Cargar y sincronizar datos
def load_and_sync_vademecum_data(force_sync: bool = False):
    enricher = AIEnricher()
    existing_news = []
    
    try:
        existing_news = db.get_all_news()
    except Exception as e:
        print(f"[Vademecum] Error leyendo SQLite: {e}")
        existing_news = []
    
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
            print(f"[Vademecum] Excepción en sincronización, cargando respaldo: {e_sync}")
            from backend.scraper import SEED_NEWS
            existing_news = SEED_NEWS
            
    return existing_news, enricher

# Botón de Sincronización en Sidebar
if st.sidebar.button("🔄 Sincronizar Radar Vademecum", use_container_width=True, type="primary"):
    with st.spinner("Rastreando portales globales de IA y enriqueciendo con Gemini AI..."):
        news_data, enricher = load_and_sync_vademecum_data(force_sync=True)
        st.session_state["just_synced"] = True
        st.rerun()
else:
    news_data, enricher = load_and_sync_vademecum_data(force_sync=False)

search_term = st.sidebar.text_input("🔍 Búsqueda global en Vademecum", placeholder="ej. Humanoides, Blackwell, MCP, LangGraph, EU AI Act...")

sources = ["Todas"] + sorted(list(set(item["source"] for item in news_data if item.get("source"))))
selected_source = st.sidebar.selectbox("🌐 Fuente tecnológica", sources)

categories = ["Todas", "ROBÓTICA & EMBODIED AI"] + [c for c in sorted(list(set(item["category"] for item in news_data if item.get("category")))) if c != "ROBÓTICA & EMBODIED AI"]
selected_category = st.sidebar.selectbox("🏷️ Categoría temática", categories)

sentiment_options = ["Todos", "Innovación", "Oportunidad", "Alerta", "Tendencia", "Actualización"]
selected_sentiment = st.sidebar.selectbox("📊 Impacto / Sentimiento", sentiment_options)

st.sidebar.markdown("---")

ai_status_color = "#10b981" if enricher.client else "#c9a227"
ai_status_text = "🟢 Gemini AI Activo" if enricher.client else "🟡 Motor Heurístico Vademecum"

sidebar_card_bg = "#161411" if is_dark else "#fdfbf7"
sidebar_card_border = "#2e2a24" if is_dark else "#e7e2d8"
sidebar_title_color = "#f4efe6" if is_dark else "#1c1917"

st.sidebar.markdown(f"""
<div style="background: {sidebar_card_bg}; border: 1px solid {sidebar_card_border}; border-radius: 10px; padding: 14px; margin-bottom: 15px;">
    <div style="font-size: 0.76rem; color: #c9a227; font-weight: 700; text-transform: uppercase;">🤖 Inteligencia Artificial</div>
    <div style="font-size: 0.9rem; color: {ai_status_color}; font-weight: 700; margin-top: 4px;">{ai_status_text}</div>
    <div style="font-size: 0.82rem; color: #a8a29e; margin-top: 8px;">💾 BD Local: <b>{len(news_data)} análisis guardados</b></div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"""
<div style="background: {sidebar_card_bg}; border: 1px solid {sidebar_card_border}; border-radius: 10px; padding: 14px;">
    <div style="font-size: 0.74rem; color: #a8a29e; font-weight: 700; text-transform: uppercase;">⚡ Plataforma</div>
    <div style="font-size: 0.88rem; color: {sidebar_title_color}; font-weight: 700; margin-top: 2px;">Vademecum Hub</div>
    <div style="font-size: 0.78rem; color: #c9a227; font-weight: 600;">Consultoría & Formación IA</div>
</div>
""", unsafe_allow_html=True)

# KPIs VADEMECUM HUB
col_k1, col_k2, col_k3, col_k4 = st.columns(4)
with col_k1:
    st.markdown(f"""
    <div class="vademecum-kpi-card">
        <div class="vademecum-kpi-label">Novedades Hoy</div>
        <div class="vademecum-kpi-value">{len(news_data)}</div>
    </div>
    """, unsafe_allow_html=True)
with col_k2:
    robotics_count = sum(1 for item in news_data if item.get("category") == "ROBÓTICA & EMBODIED AI")
    st.markdown(f"""
    <div class="vademecum-kpi-card" style="border-color: rgba(201, 162, 39, 0.6);">
        <div class="vademecum-kpi-label" style="color: #c9a227;">Robótica & Embodied 🦾</div>
        <div class="vademecum-kpi-value" style="color: #c9a227;">{robotics_count}</div>
    </div>
    """, unsafe_allow_html=True)
with col_k3:
    fav_count = len(st.session_state["favorites"])
    st.markdown(f"""
    <div class="vademecum-kpi-card">
        <div class="vademecum-kpi-label">Artículos Guardados ⭐</div>
        <div class="vademecum-kpi-value" style="color: #e5be38;">{fav_count}</div>
    </div>
    """, unsafe_allow_html=True)
with col_k4:
    sources_count = len(set(item["source"] for item in news_data if item.get("source")))
    st.markdown(f"""
    <div class="vademecum-kpi-card">
        <div class="vademecum-kpi-label">Fuentes Globales 🌐</div>
        <div class="vademecum-kpi-value" style="color: #2f6f6a;">{sources_count}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Tendencias Rápidas
st.markdown("##### 🔥 Temáticas de Vanguardia en Vademecum:")
tag_cols = st.columns(6)
all_tags = ["Todos", "#Robótica", "#LLMs", "#HardwareNVIDIA", "#AgentesIA", "#EUAIAct"]
for i, tag in enumerate(all_tags):
    if tag_cols[i].button(tag, key=f"btn_vademecum_tag_{i}", use_container_width=True):
        st.session_state["selected_tag"] = tag

# Pestañas Principales
tab_feed, tab_chat, tab_favorites, tab_digest = st.tabs([
    "📰 Radar Vademecum", 
    "🤖 Asistente Vademecum (Chat RAG)", 
    "⭐ Artículos Guardados", 
    "📝 Vademecum Daily Briefing"
])

# Filtrado de Noticias
filtered_news = news_data
unique_news = []
seen_ids = set()
for item in filtered_news:
    if item["id"] not in seen_ids:
        seen_ids.add(item["id"])
        unique_news.append(item)
filtered_news = unique_news

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

# Función para renderizar tarjeta Vademecum
def render_vademecum_card(item: dict, key_prefix: str = "feed"):
    is_robotics = item.get("category") == "ROBÓTICA & EMBODIED AI"
    card_class = "vademecum-card vademecum-card-robotics" if is_robotics else "vademecum-card"
    category_badge_class = "badge-robotics-category" if is_robotics else "badge-category"
    
    sentiment = item.get("sentiment", "Innovación")
    if sentiment in ["Innovación", "Oportunidad"]:
        tone_badge_class = "badge-tone-innovation"
    elif sentiment == "Alerta":
        tone_badge_class = "badge-tone-alert"
    else:
        tone_badge_class = "badge-tone-trend"
        
    is_fav = item["id"] in st.session_state["favorites"]
    fav_icon = "⭐ Guardada" if is_fav else "☆ Guardar"

    c_card, c_action = st.columns([0.88, 0.12])
    with c_card:
        hashtags_display = ' '.join(item.get('hashtags', [])) if isinstance(item.get('hashtags'), list) else ""
        action_btn_style = "text-decoration: none; font-weight: 700; color: #c9a227; font-size: 0.88rem; background: rgba(201, 162, 39, 0.12); padding: 6px 14px; border-radius: 8px; border: 1px solid rgba(201, 162, 39, 0.35);" if is_dark else "text-decoration: none; font-weight: 700; color: #b08a1c; font-size: 0.88rem; background: #fdfaf2; padding: 6px 14px; border-radius: 8px; border: 1px solid #d4af37;"
        tag_color = "#c9a227" if is_dark else "#b08a1c"
        date_color = "#a8a29e" if is_dark else "#78716c"
        
        st.markdown(f"""
        <div class="{card_class}">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span class="badge-source">🌐 {item.get('source', 'Fuente')}</span>
                    <span class="{category_badge_class}">⚡ {item.get('category', 'IA')}</span>
                    <span class="{tone_badge_class}">{item.get('sentiment_badge', '🚀 Innovación')}</span>
                </div>
                <div style="font-size: 0.82rem; color: {date_color}; font-weight: 600; font-family: 'IBM Plex Mono', monospace;">
                    📅 {item.get('date', today_date_str)}
                </div>
            </div>
            
            <a href="{item.get('url', '#')}" target="_blank" class="news-title-link">
                {item.get('title', 'Sin título')}
            </a>
            
            <div class="news-summary-text">
                {item.get('summary', '')}
            </div>
            
            <div style="margin-top: 16px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div style="font-size: 0.82rem; color: {tag_color}; font-weight: 700;">
                    {hashtags_display}
                </div>
                <a href="{item.get('url', '#')}" target="_blank" style="{action_btn_style}">
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
                st.toast(f"Artículo eliminado de guardados", icon="🗑️")
            else:
                db.add_favorite(item["id"])
                st.session_state["favorites"].append(item["id"])
                st.toast(f"Artículo guardado en Vademecum", icon="⭐")
            st.rerun()

# PESTAÑA 1: RADAR VADEMECUM
with tab_feed:
    st.markdown(f"#### 📡 **{len(filtered_news)}** novedades tecnológicas en el Radar")
    if not filtered_news:
        st.info("No se han encontrado novedades que coincidan con los filtros seleccionados.")
    else:
        for item in filtered_news:
            render_vademecum_card(item, key_prefix="main_feed")

# PESTAÑA 2: ASISTENTE VADEMECUM (CHAT RAG)
with tab_chat:
    st.markdown("### 🤖 Asistente de Consultoría Vademecum Hub")
    st.markdown("Analiza la colección de noticias para resolver dudas técnicas, comparar arquitecturas de modelos o evaluar impacto de negocio para clientes de consultoría.")
    
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        if st.button("🦾 ¿Qué avances recientes hay en robots humanoides y manipulación?", use_container_width=True, key="vad_sug_1"):
            st.session_state["chat_history"].append({"role": "user", "text": "¿Qué avances recientes hay en robots humanoides y manipulación industrial?"})
            with st.spinner("Consultando fuentes con Gemini AI..."):
                ans = enricher.ask_feed("¿Qué avances recientes hay en robots humanoides y manipulación industrial?", news_data)
                st.session_state["chat_history"].append({"role": "assistant", "text": ans})
                st.rerun()
        if st.button("💻 ¿Cuáles son las novedades en GPUs, clusters y hardware NVIDIA?", use_container_width=True, key="vad_sug_2"):
            st.session_state["chat_history"].append({"role": "user", "text": "¿Cuáles son las novedades en GPUs, clusters y hardware NVIDIA?"})
            with st.spinner("Consultando fuentes con Gemini AI..."):
                ans = enricher.ask_feed("¿Cuáles son las novedades en GPUs, clusters y hardware NVIDIA?", news_data)
                st.session_state["chat_history"].append({"role": "assistant", "text": ans})
                st.rerun()
    with col_q2:
        if st.button("🛠️ ¿Cómo impacta Model Context Protocol (MCP) en arquitecturas de agentes?", use_container_width=True, key="vad_sug_3"):
            st.session_state["chat_history"].append({"role": "user", "text": "¿Cómo impacta Model Context Protocol (MCP) en arquitecturas de agentes?"})
            with st.spinner("Consultando fuentes con Gemini AI..."):
                ans = enricher.ask_feed("¿Cómo impacta Model Context Protocol (MCP) en arquitecturas de agentes?", news_data)
                st.session_state["chat_history"].append({"role": "assistant", "text": ans})
                st.rerun()
        if st.button("⚖️ ¿Qué requisitos exige el EU AI Act para sistemas en clientes corporativos?", use_container_width=True, key="vad_sug_4"):
            st.session_state["chat_history"].append({"role": "user", "text": "¿Qué requisitos exige el EU AI Act para sistemas en clientes corporativos?"})
            with st.spinner("Consultando fuentes con Gemini AI..."):
                ans = enricher.ask_feed("¿Qué requisitos exige el EU AI Act para sistemas en clientes corporativos?", news_data)
                st.session_state["chat_history"].append({"role": "assistant", "text": ans})
                st.rerun()

    st.markdown("---")
    
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.markdown(f"**👤 Consultor Vademecum:** {msg['text']}")
        else:
            st.markdown(msg['text'])
            st.markdown("---")
            
    user_query = st.text_input("💬 Consulta estratégica o técnica:", placeholder="Ej. ¿Qué modelos son más recomendables para despliegue local en banca o sanidad?", key="vad_rag_input")
    if st.button("Consultar Asistente Vademecum", type="primary", key="vad_btn_send"):
        if user_query.strip():
            st.session_state["chat_history"].append({"role": "user", "text": user_query})
            with st.spinner("Analizando con Gemini AI..."):
                ans = enricher.ask_feed(user_query, news_data)
                st.session_state["chat_history"].append({"role": "assistant", "text": ans})
                st.rerun()

# PESTAÑA 3: MIS FAVORITOS
with tab_favorites:
    st.markdown("### ⭐ Artículos Guardados en Vademecum")
    fav_items = [item for item in news_data if item["id"] in st.session_state["favorites"]]
    if not fav_items:
        st.info("Aún no tienes artículos guardados. Pulsa en '☆ Guardar' en cualquier tarjeta para agregarlo a tu dossier.")
    else:
        st.markdown(f"Tienes **{len(fav_items)} artículos** guardados:")
        for item in fav_items:
            render_vademecum_card(item, key_prefix="fav_tab")

# PESTAÑA 4: MORNING BRIEFING
with tab_digest:
    st.markdown("### 📝 Vademecum Daily AI Briefing")
    st.markdown("Genera un informe ejecutivo matinal estructurado en Markdown para el equipo de consultoría y clientes.")
    
    if st.button("⚡ Compilar Daily Briefing de Hoy", type="primary", key="vad_btn_gen_digest"):
        with st.spinner("Compilando análisis ejecutivo de IA y Robótica..."):
            digest_content = enricher.generate_daily_digest(news_data)
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

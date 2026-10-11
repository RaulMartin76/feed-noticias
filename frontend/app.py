import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
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
    page_title="Terminal IA & Robótica • Feed de Inteligencia Tecnológica",
    page_icon="🤖",
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

# Cargar favoritos desde la base de datos
st.session_state["favorites"] = db.get_favorites()

# --- SIDEBAR: PANEL DE CONTROL ---
st.sidebar.markdown("### 🎛️ Terminal de Control")

# Selector de Tema
theme_mode = st.sidebar.radio(
    "🎨 Visualización",
    ["🌙 Modo Cyber Dark", "☀️ Modo Tech Light"],
    index=0 if st.session_state["theme"] == "dark" else 1,
    horizontal=True
)
st.session_state["theme"] = "dark" if "Dark" in theme_mode else "light"
is_dark = st.session_state["theme"] == "dark"

# DESIGN SYSTEM - Estilos CSS Avanzados para Consultoría de IA y Robótica
if is_dark:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

        html, body, [data-testid="stAppViewContainer"] {
            background-color: #070913 !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            color: #f1f5f9 !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: #0c1020 !important;
            border-right: 1px solid rgba(0, 210, 255, 0.15) !important;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #ffffff !important;
            font-weight: 600 !important;
        }

        div[data-testid="stTextInput"] input,
        .stTextInput input,
        input[type="text"],
        textarea {
            background-color: #0e1428 !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            border: 1px solid rgba(0, 210, 255, 0.35) !important;
            border-radius: 10px !important;
            padding: 10px 16px !important;
            font-size: 0.98rem !important;
            font-weight: 600 !important;
        }

        div[data-testid="stTextInput"] input:focus,
        .stTextInput input:focus,
        input[type="text"]:focus,
        textarea:focus {
            background-color: #151d38 !important;
            border-color: #00d2ff !important;
            box-shadow: 0 0 14px rgba(0, 210, 255, 0.4) !important;
            outline: none !important;
        }

        .hero-header {
            background: linear-gradient(135deg, rgba(12, 16, 32, 0.95) 0%, rgba(20, 28, 55, 0.85) 50%, rgba(12, 16, 32, 0.95) 100%);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(0, 210, 255, 0.2);
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(0, 210, 255, 0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        .hero-title {
            font-family: 'Outfit', sans-serif;
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff 0%, #00d2ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            letter-spacing: -0.02em;
        }
        .hero-subtitle {
            color: #94a3b8;
            font-size: 0.98rem;
            margin-top: 6px;
            margin-bottom: 0;
            font-weight: 500;
        }

        .hero-dates-box {
            display: flex;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(0, 210, 255, 0.25);
            border-radius: 12px;
            padding: 10px 18px;
            gap: 16px;
        }
        .hero-date-item {
            display: flex;
            flex-direction: column;
        }
        .hero-date-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            color: #00d2ff;
            font-weight: 700;
            letter-spacing: 0.05em;
        }
        .hero-date-val {
            font-size: 0.95rem;
            font-weight: 800;
            color: #ffffff;
            font-family: 'JetBrains Mono', monospace;
        }

        .kpi-card {
            background: rgba(14, 20, 40, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 18px 22px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            border-color: rgba(0, 210, 255, 0.4);
        }
        .kpi-label {
            font-size: 0.8rem;
            color: #94a3b8;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .kpi-value {
            font-size: 1.85rem;
            font-weight: 800;
            color: #ffffff;
            font-family: 'Outfit', sans-serif;
            margin-top: 4px;
        }

        .news-card-container {
            background: rgba(14, 20, 40, 0.65);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
        }
        .news-card-container:hover {
            transform: translateY(-3px);
            border-color: rgba(0, 210, 255, 0.5);
            box-shadow: 0 10px 30px -5px rgba(0, 210, 255, 0.2);
        }
        
        .news-card-robotics {
            background: linear-gradient(135deg, rgba(30, 10, 45, 0.8) 0%, rgba(14, 20, 40, 0.85) 100%) !important;
            border: 1px solid rgba(224, 36, 195, 0.5) !important;
            box-shadow: 0 4px 24px rgba(224, 36, 195, 0.15) !important;
        }
        .news-card-robotics:hover {
            border-color: #e024c3 !important;
            box-shadow: 0 10px 30px -5px rgba(224, 36, 195, 0.35) !important;
        }

        .badge-source {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: #94a3b8;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 600;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-category {
            background: rgba(0, 210, 255, 0.12);
            border: 1px solid rgba(0, 210, 255, 0.35);
            color: #38bdf8;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-robotics-category {
            background: linear-gradient(135deg, #c026d3 0%, #db2777 100%) !important;
            color: #ffffff !important;
            padding: 5px 14px !important;
            border-radius: 8px !important;
            font-size: 0.8rem !important;
            font-weight: 800 !important;
            box-shadow: 0 2px 10px rgba(219, 39, 119, 0.4) !important;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-tone-innovation {
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(52, 211, 153, 0.4);
            color: #34d399;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-tone-alert {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(248, 113, 113, 0.4);
            color: #f87171;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-tone-trend {
            background: rgba(245, 158, 11, 0.15);
            border: 1px solid rgba(251, 191, 36, 0.4);
            color: #fbbf24;
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
            color: #f8fafc;
            text-decoration: none;
            margin-top: 12px;
            margin-bottom: 10px;
            display: block;
            transition: color 0.2s ease;
        }
        .news-title-link:hover {
            color: #00d2ff;
        }
        .news-summary-text {
            color: #cbd5e1;
            font-size: 0.98rem;
            line-height: 1.6;
            white-space: pre-line;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    # MODO TECH LIGHT
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

        html, body, [data-testid="stAppViewContainer"] {
            background-color: #f8fafc !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            color: #0f172a !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0 !important;
        }

        .hero-header {
            background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 50%, #e2e8f0 100%);
            border: 1px solid #cbd5e1;
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 25px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        .hero-title {
            font-family: 'Outfit', sans-serif;
            font-size: 2.2rem;
            font-weight: 800;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            margin: 0;
            letter-spacing: -0.02em;
        }
        .hero-subtitle {
            color: #475569;
            font-size: 0.98rem;
            margin-top: 6px;
            margin-bottom: 0;
            font-weight: 600;
        }

        .hero-dates-box {
            display: flex;
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 10px 18px;
            gap: 16px;
        }
        .hero-date-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            color: #0284c7;
            font-weight: 700;
            letter-spacing: 0.05em;
        }
        .hero-date-val {
            font-size: 0.95rem;
            font-weight: 800;
            color: #0f172a;
            font-family: 'JetBrains Mono', monospace;
        }

        .kpi-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 18px 22px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
        }
        .kpi-label {
            font-size: 0.8rem;
            color: #64748b;
            font-weight: 700;
            text-transform: uppercase;
        }
        .kpi-value {
            font-size: 1.85rem;
            font-weight: 800;
            color: #0f172a;
            font-family: 'Outfit', sans-serif;
            margin-top: 4px;
        }

        .news-card-container {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
            transition: all 0.25s ease;
        }
        .news-card-container:hover {
            transform: translateY(-3px);
            border-color: #0284c7;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        }
        
        .news-card-robotics {
            background: linear-gradient(135deg, #fdf2f8 0%, #ffffff 100%) !important;
            border: 1px solid #f472b6 !important;
            box-shadow: 0 4px 18px rgba(236, 72, 153, 0.1) !important;
        }

        .badge-source {
            background: #f1f5f9;
            border: 1px solid #cbd5e1;
            color: #334155;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 600;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-category {
            background: #e0f2fe;
            border: 1px solid #7dd3fc;
            color: #0369a1;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-robotics-category {
            background: linear-gradient(135deg, #d946ef 0%, #db2777 100%) !important;
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
            color: #0f172a;
            text-decoration: none;
            margin-top: 12px;
            margin-bottom: 10px;
            display: block;
        }
        .news-title-link:hover {
            color: #0284c7;
        }
        .news-summary-text {
            color: #334155;
            font-size: 0.98rem;
            line-height: 1.6;
            white-space: pre-line;
        }
    </style>
    """, unsafe_allow_html=True)

# Header Principal Hero con Fechas y Título
today_date_str = datetime.now().strftime("%d/%m/%Y")
last_update_str = st.session_state["last_updated"]

st.markdown(f"""
<div class="hero-header">
    <div>
        <div class="hero-title">⚡ Terminal IA & Robótica • Consultoría Tecnológica</div>
        <div class="hero-subtitle">Inteligencia Global en Tiempo Real • Modelos Fundacionales • Hardware • Agentes • <b style="color: #e024c3;">ROBÓTICA & EMBODIED AI</b></div>
    </div>
    <div class="hero-dates-box">
        <div class="hero-date-item">
            <span class="hero-date-label">📅 Fecha Actual</span>
            <span class="hero-date-val">{today_date_str}</span>
        </div>
        <div style="width: 1px; background: rgba(128,128,128,0.25); margin: 0 4px;"></div>
        <div class="hero-date-item">
            <span class="hero-date-label">⏱️ Última Sincronización</span>
            <span class="hero-date-val">{last_update_str}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if st.session_state["just_synced"]:
    st.toast("⚡ Noticias de IA y Robótica resincronizadas con éxito desde fuentes globales", icon="🚀")
    st.success("Noticias de IA y Robótica resincronizadas con éxito desde fuentes globales.")
    st.session_state["just_synced"] = False

# Función para sincronizar noticias de IA
def load_and_sync_ai_data(force_sync: bool = False):
    enricher = AIEnricher()
    existing_news = []
    
    try:
        existing_news = db.get_all_news()
    except Exception as e:
        print(f"[App IA] Error leyendo SQLite: {e}")
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
            print(f"[App IA] Excepción en sincronización, cargando respaldo: {e_sync}")
            from backend.scraper import SEED_NEWS
            existing_news = SEED_NEWS
            
    return existing_news, enricher

# Botón de Sincronización en Sidebar
if st.sidebar.button("🔄 Sincronizar Noticias Globales", use_container_width=True, type="primary"):
    with st.spinner("Rastreando portales top de IA & Robótica y enriqueciendo con Gemini AI..."):
        news_data, enricher = load_and_sync_ai_data(force_sync=True)
        st.session_state["just_synced"] = True
        st.rerun()
else:
    news_data, enricher = load_and_sync_ai_data(force_sync=False)

search_term = st.sidebar.text_input("🔍 Búsqueda global", placeholder="ej. Humanoides, Blackwell, MCP, LangGraph, EU AI Act...")

sources = ["Todas"] + sorted(list(set(item["source"] for item in news_data if item.get("source"))))
selected_source = st.sidebar.selectbox("🌐 Fuente tecnológica", sources)

categories = ["Todas", "ROBÓTICA & EMBODIED AI"] + [c for c in sorted(list(set(item["category"] for item in news_data if item.get("category")))) if c != "ROBÓTICA & EMBODIED AI"]
selected_category = st.sidebar.selectbox("🏷️ Categoría temática", categories)

sentiment_options = ["Todos", "Innovación", "Oportunidad", "Alerta", "Tendencia", "Actualización"]
selected_sentiment = st.sidebar.selectbox("📊 Impacto / Sentimiento", sentiment_options)

st.sidebar.markdown("---")

ai_status_color = "#10b981" if enricher.client else "#f59e0b"
ai_status_text = "🟢 Gemini AI Activo" if enricher.client else "🟡 Motor Heurístico"

sidebar_card_bg = "rgba(14, 20, 40, 0.9)" if is_dark else "#f1f5f9"
sidebar_card_border = "rgba(0, 210, 255, 0.2)" if is_dark else "#cbd5e1"
sidebar_title_color = "#ffffff" if is_dark else "#0f172a"

st.sidebar.markdown(f"""
<div style="background: {sidebar_card_bg}; border: 1px solid {sidebar_card_border}; border-radius: 10px; padding: 14px; margin-bottom: 15px;">
    <div style="font-size: 0.8rem; color: {sidebar_title_color}; font-weight: 700; text-transform: uppercase;">🤖 Inteligencia Artificial</div>
    <div style="font-size: 0.9rem; color: {ai_status_color}; font-weight: 700; margin-top: 4px;">{ai_status_text}</div>
    <div style="font-size: 0.82rem; color: #00d2ff; margin-top: 8px;">💾 BD Local: <b>{len(news_data)} artículos analizados</b></div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"""
<div style="background: {sidebar_card_bg}; border: 1px solid {sidebar_card_border}; border-radius: 10px; padding: 14px;">
    <div style="font-size: 0.75rem; color: #64748b; font-weight: 700; text-transform: uppercase;">🏢 Entorno</div>
    <div style="font-size: 0.88rem; color: {sidebar_title_color}; font-weight: 700; margin-top: 2px;">Consultoría de IA & Robótica</div>
    <div style="font-size: 0.78rem; color: #00d2ff; font-weight: 600;">Inteligencia Tecnológica</div>
</div>
""", unsafe_allow_html=True)

# KPIs Principales
col_k1, col_k2, col_k3, col_k4 = st.columns(4)
with col_k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Noticias Totales Hoy</div>
        <div class="kpi-value">{len(news_data)}</div>
    </div>
    """, unsafe_allow_html=True)
with col_k2:
    robotics_count = sum(1 for item in news_data if item.get("category") == "ROBÓTICA & EMBODIED AI")
    st.markdown(f"""
    <div class="kpi-card" style="border-color: {'rgba(224, 36, 195, 0.5)' if is_dark else '#f472b6'};">
        <div class="kpi-label" style="color: #e024c3;">Robótica & Embodied 🦾</div>
        <div class="kpi-value" style="color: #ec4899;">{robotics_count}</div>
    </div>
    """, unsafe_allow_html=True)
with col_k3:
    fav_count = len(st.session_state["favorites"])
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Mis Favoritos ⭐</div>
        <div class="kpi-value" style="color: #fbbf24;">{fav_count}</div>
    </div>
    """, unsafe_allow_html=True)
with col_k4:
    sources_count = len(set(item["source"] for item in news_data if item.get("source")))
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Fuentes Globales 🌐</div>
        <div class="kpi-value" style="color: #00d2ff;">{sources_count}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Filtro de Tendencias Rápidas
st.markdown("##### 🔥 Temáticas Clave & Tendencias Tecnológicas:")
tag_cols = st.columns(6)
all_tags = ["Todos", "#Robótica", "#LLMs", "#HardwareNVIDIA", "#AgentesIA", "#EUAIAct"]
for i, tag in enumerate(all_tags):
    if tag_cols[i].button(tag, key=f"btn_ai_tag_{i}", use_container_width=True):
        st.session_state["selected_tag"] = tag

# Pestañas Principales
tab_feed, tab_chat, tab_favorites, tab_digest = st.tabs([
    "📰 Feed IA & Robótica", 
    "🤖 Asistente Consultoría (Chat RAG)", 
    "⭐ Artículos Guardados", 
    "📝 Morning AI Briefing"
])

# Filtrado de Artículos
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

# Renderizado de Tarjeta de Noticia
def render_ai_news_card(item: dict, key_prefix: str = "feed"):
    is_robotics = item.get("category") == "ROBÓTICA & EMBODIED AI"
    card_class = "news-card-container news-card-robotics" if is_robotics else "news-card-container"
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
        action_btn_style = "text-decoration: none; font-weight: 700; color: #00d2ff; font-size: 0.88rem; background: rgba(0, 210, 255, 0.1); padding: 6px 14px; border-radius: 8px; border: 1px solid rgba(0, 210, 255, 0.25);" if is_dark else "text-decoration: none; font-weight: 700; color: #0284c7; font-size: 0.88rem; background: #e0f2fe; padding: 6px 14px; border-radius: 8px; border: 1px solid #7dd3fc;"
        tag_color = "#00d2ff" if is_dark else "#0284c7"
        date_color = "#94a3b8" if is_dark else "#64748b"
        
        st.markdown(f"""
        <div class="{card_class}">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span class="badge-source">🌐 {item.get('source', 'Fuente')}</span>
                    <span class="{category_badge_class}">⚡ {item.get('category', 'IA')}</span>
                    <span class="{tone_badge_class}">{item.get('sentiment_badge', '🚀 Innovación')}</span>
                </div>
                <div style="font-size: 0.82rem; color: {date_color}; font-weight: 600;">
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
        btn_key = f"fav_btn_{key_prefix}_{item['id']}"
        if st.button(fav_icon, key=btn_key, use_container_width=True):
            if is_fav:
                db.remove_favorite(item["id"])
                st.session_state["favorites"].remove(item["id"])
                st.toast(f"Artículo eliminado de favoritos", icon="🗑️")
            else:
                db.add_favorite(item["id"])
                st.session_state["favorites"].append(item["id"])
                st.toast(f"Artículo guardado en favoritos", icon="⭐")
            st.rerun()

# PESTAÑA 1: FEED DE NOTICIAS
with tab_feed:
    st.markdown(f"#### 📡 Mostrando **{len(filtered_news)}** novedades tecnológicas")
    if not filtered_news:
        st.info("No se han encontrado noticias que coincidan con los filtros seleccionados.")
    else:
        for item in filtered_news:
            render_ai_news_card(item, key_prefix="main_feed")

# PESTAÑA 2: ASISTENTE CONSULTORÍA (CHAT RAG)
with tab_chat:
    st.markdown("### 🤖 Asistente Estratégico de Consultoría de IA & Robótica")
    st.markdown("Formula preguntas sobre modelos de lenguaje, infraestructura de cómputo, directivas regulatorias o robótica humanoide con base en las noticias capturadas.")
    
    # Preguntas sugeridas
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        if st.button("🦾 ¿Qué avances recientes hay en robots humanoides y manipulación?", use_container_width=True, key="btn_sug_1"):
            st.session_state["chat_history"].append({"role": "user", "text": "¿Qué avances recientes hay en robots humanoides y manipulación industrial?"})
            with st.spinner("Analizando fuentes del feed con Gemini AI..."):
                ans = enricher.ask_feed("¿Qué avances recientes hay en robots humanoides y manipulación industrial?", news_data)
                st.session_state["chat_history"].append({"role": "assistant", "text": ans})
                st.rerun()
        if st.button("💻 ¿Cuáles son las novedades en GPUs, clusters y hardware NVIDIA?", use_container_width=True, key="btn_sug_2"):
            st.session_state["chat_history"].append({"role": "user", "text": "¿Cuáles son las novedades en GPUs, clusters y hardware NVIDIA?"})
            with st.spinner("Analizando fuentes del feed con Gemini AI..."):
                ans = enricher.ask_feed("¿Cuáles son las novedades en GPUs, clusters y hardware NVIDIA?", news_data)
                st.session_state["chat_history"].append({"role": "assistant", "text": ans})
                st.rerun()
    with col_q2:
        if st.button("🛠️ ¿Cómo impacta Model Context Protocol (MCP) en arquitecturas de agentes?", use_container_width=True, key="btn_sug_3"):
            st.session_state["chat_history"].append({"role": "user", "text": "¿Cómo impacta Model Context Protocol (MCP) en arquitecturas de agentes?"})
            with st.spinner("Analizando fuentes del feed con Gemini AI..."):
                ans = enricher.ask_feed("¿Cómo impacta Model Context Protocol (MCP) en arquitecturas de agentes?", news_data)
                st.session_state["chat_history"].append({"role": "assistant", "text": ans})
                st.rerun()
        if st.button("⚖️ ¿Qué requisitos exige el EU AI Act para sistemas en clientes corporativos?", use_container_width=True, key="btn_sug_4"):
            st.session_state["chat_history"].append({"role": "user", "text": "¿Qué requisitos exige el EU AI Act para sistemas en clientes corporativos?"})
            with st.spinner("Analizando fuentes del feed con Gemini AI..."):
                ans = enricher.ask_feed("¿Qué requisitos exige el EU AI Act para sistemas en clientes corporativos?", news_data)
                st.session_state["chat_history"].append({"role": "assistant", "text": ans})
                st.rerun()

    st.markdown("---")
    
    # Historial de conversación
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.markdown(f"**👤 Consultor:** {msg['text']}")
        else:
            st.markdown(msg['text'])
            st.markdown("---")
            
    user_query = st.text_input("💬 Consulta técnica o estratégica:", placeholder="Ej. ¿Qué modelos de código abierto son más eficientes para despliegue local?", key="rag_user_input")
    if st.button("Enviar Consulta", type="primary", key="btn_send_rag"):
        if user_query.strip():
            st.session_state["chat_history"].append({"role": "user", "text": user_query})
            with st.spinner("Evaluando feed y generando dictamen técnico..."):
                ans = enricher.ask_feed(user_query, news_data)
                st.session_state["chat_history"].append({"role": "assistant", "text": ans})
                st.rerun()

# PESTAÑA 3: MIS FAVORITOS
with tab_favorites:
    st.markdown("### ⭐ Artículos de IA Guardados para Análisis")
    fav_items = [item for item in news_data if item["id"] in st.session_state["favorites"]]
    if not fav_items:
        st.info("Aún no tienes artículos guardados. Pulsa en el botón '☆ Guardar' de cualquier tarjeta para agregarlo a esta lista.")
    else:
        st.markdown(f"Tienes **{len(fav_items)} artículos** marcados:")
        for item in fav_items:
            render_ai_news_card(item, key_prefix="fav_tab")

# PESTAÑA 4: MORNING AI BRIEFING
with tab_digest:
    st.markdown("### 📝 Generador de Morning AI Briefing Ejecutivo")
    st.markdown("Compila instantáneamente un informe diario en formato Markdown para compartir en canales de Slack, Teams o preparar la reunión diaria del equipo de consultoría.")
    
    if st.button("⚡ Generar Informe de Hoy", type="primary", key="btn_gen_digest"):
        with st.spinner("Compilando análisis de novedades de IA y Robótica..."):
            digest_content = enricher.generate_daily_digest(news_data)
            st.session_state["generated_digest"] = digest_content
            
    if "generated_digest" in st.session_state:
        st.markdown("---")
        st.download_button(
            label="📥 Descargar Briefing (.md)",
            data=st.session_state["generated_digest"],
            file_name=f"morning_ai_briefing_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            key="btn_download_digest"
        )
        st.markdown(st.session_state["generated_digest"])

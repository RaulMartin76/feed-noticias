import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

# Cargar variables del entorno desde .env oculto
load_dotenv()

# Permitir importación directa del backend en cualquier entorno
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

REPO_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.scraper import fetch_live_news
from backend.ai_enricher import AIEnricher
from backend.db_manager import DatabaseManager
from backend.gmail_reader import GmailNewsletterReader

st.set_page_config(
    page_title="Terminal Financiero • Feed de Noticias",
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

# Cargar favoritos desde la base de datos
st.session_state["favorites"] = db.get_favorites()

# --- SIDEBAR: PANEL DE CONTROL ---
st.sidebar.markdown("### 🎛️ Panel de Control")

# Selector de Tema
theme_mode = st.sidebar.radio(
    "🎨 Modo de Visualización",
    ["🌙 Modo Oscuro", "☀️ Modo Claro"],
    index=0 if st.session_state["theme"] == "dark" else 1,
    horizontal=True
)
st.session_state["theme"] = "dark" if "Oscuro" in theme_mode else "light"
is_dark = st.session_state["theme"] == "dark"

# DESIGN SYSTEM - CSS Avanzado Adaptativo (Modo Oscuro Glassmorphism & Modo Claro Executive)
if is_dark:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;600;700;800&display=swap');

        html, body, [data-testid="stAppViewContainer"] {
            background-color: #070a12 !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            color: #f1f5f9 !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: #0d1322 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
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
            background-color: #0f172a !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            border: 1px solid rgba(56, 189, 248, 0.4) !important;
            border-radius: 10px !important;
            padding: 10px 16px !important;
            font-size: 0.98rem !important;
            font-weight: 600 !important;
        }

        div[data-testid="stTextInput"] input:focus,
        .stTextInput input:focus,
        input[type="text"]:focus,
        textarea:focus {
            background-color: #1e293b !important;
            border-color: #38bdf8 !important;
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.4) !important;
            outline: none !important;
        }

        .hero-header {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.85) 50%, rgba(15, 23, 42, 0.95) 100%);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.15);
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
            background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
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
            gap: 12px;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(56, 189, 248, 0.25);
            padding: 10px 18px;
            border-radius: 12px;
        }
        .hero-date-label {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            color: #94a3b8;
        }
        .hero-date-val {
            font-family: 'Outfit', sans-serif;
            font-size: 1.05rem;
            font-weight: 700;
            color: #38bdf8;
        }

        [data-testid="stTabs"] *,
        [data-baseweb="tab-list"] *,
        [data-baseweb="tab"] * {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            font-weight: 700 !important;
        }

        [data-baseweb="tab"][aria-selected="false"],
        [data-testid="stTabs"] button[aria-selected="false"] {
            background-color: #1e293b !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 8px !important;
            margin-right: 8px !important;
            padding: 8px 22px !important;
        }

        [data-baseweb="tab"][aria-selected="true"],
        [data-testid="stTabs"] button[aria-selected="true"] {
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
            border: 1px solid #38bdf8 !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 15px rgba(14, 165, 233, 0.5) !important;
        }

        div[data-testid="stButton"] > button {
            background: #1e293b !important;
            border: 1px solid rgba(56, 189, 248, 0.3) !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stButton"] > button * {
            color: #38bdf8 !important;
            font-weight: 700 !important;
            font-size: 0.88rem !important;
        }
        div[data-testid="stButton"] > button:hover {
            background: #0284c7 !important;
            border-color: #38bdf8 !important;
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.4) !important;
        }
        div[data-testid="stButton"] > button:hover * {
            color: #ffffff !important;
        }

        .kpi-card {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 18px 22px;
            text-align: left;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            transition: all 0.25s ease;
        }
        .kpi-card:hover {
            border-color: rgba(56, 189, 248, 0.4);
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 163, 224, 0.15);
        }
        .kpi-label {
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #94a3b8;
            margin-bottom: 6px;
        }
        .kpi-value {
            font-family: 'Outfit', sans-serif;
            font-size: 2rem;
            font-weight: 800;
            color: #f8fafc;
        }

        .news-card-container {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        }
        .news-card-container:hover {
            transform: translateY(-4px);
            border-color: rgba(56, 189, 248, 0.35);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4), 0 0 20px rgba(56, 189, 248, 0.1);
        }
        
        .news-card-alt {
            background: linear-gradient(135deg, rgba(30, 11, 28, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%) !important;
            border: 1px solid rgba(236, 72, 153, 0.35) !important;
            box-shadow: 0 4px 25px rgba(236, 72, 153, 0.15) !important;
        }

        .badge-source {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: #cbd5e1;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 600;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-category {
            background: rgba(14, 165, 233, 0.15);
            border: 1px solid rgba(56, 189, 248, 0.3);
            color: #38bdf8;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-alt-category {
            background: linear-gradient(135deg, #d946ef 0%, #ec4899 100%) !important;
            color: #ffffff !important;
            padding: 5px 14px !important;
            border-radius: 8px !important;
            font-size: 0.8rem !important;
            font-weight: 800 !important;
            box-shadow: 0 0 12px rgba(217, 70, 239, 0.5) !important;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-tone-opportunity {
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
        .badge-tone-neutral {
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
            color: #38bdf8;
        }
        .news-summary-text {
            color: #cbd5e1;
            font-size: 0.98rem;
            line-height: 1.6;
            white-space: pre-line;
        }

        .disclaimer-card {
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 14px;
            padding: 24px;
            margin-top: 40px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
    </style>
    """, unsafe_allow_html=True)
else:
    # CSS MODO CLARO EXECUTIVE
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;600;700;800&display=swap');

        html, body, [data-testid="stAppViewContainer"] {
            background-color: #f8fafc !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            color: #0f172a !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0 !important;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #0f172a !important;
            font-weight: 600 !important;
        }

        div[data-testid="stTextInput"] input,
        .stTextInput input,
        input[type="text"],
        textarea {
            background-color: #ffffff !important;
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 10px !important;
            padding: 10px 16px !important;
            font-size: 0.98rem !important;
            font-weight: 600 !important;
        }

        div[data-testid="stTextInput"] input:focus,
        .stTextInput input:focus,
        input[type="text"]:focus,
        textarea:focus {
            background-color: #f8fafc !important;
            border-color: #0284c7 !important;
            box-shadow: 0 0 10px rgba(2, 132, 199, 0.2) !important;
            outline: none !important;
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
            gap: 12px;
            background: #ffffff;
            border: 1px solid #cbd5e1;
            padding: 10px 18px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .hero-date-label {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            color: #64748b;
        }
        .hero-date-val {
            font-family: 'Outfit', sans-serif;
            font-size: 1.05rem;
            font-weight: 700;
            color: #0284c7;
        }

        [data-testid="stTabs"] *,
        [data-baseweb="tab-list"] *,
        [data-baseweb="tab"] * {
            font-weight: 700 !important;
        }

        [data-baseweb="tab"][aria-selected="false"],
        [data-testid="stTabs"] button[aria-selected="false"] {
            background-color: #e2e8f0 !important;
            border: 1px solid #cbd5e1 !important;
            color: #1e293b !important;
            -webkit-text-fill-color: #1e293b !important;
            border-radius: 8px !important;
            margin-right: 8px !important;
            padding: 8px 22px !important;
        }

        [data-baseweb="tab"][aria-selected="true"],
        [data-testid="stTabs"] button[aria-selected="true"] {
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            border: 1px solid #0284c7 !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3) !important;
        }

        div[data-testid="stButton"] > button {
            background: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stButton"] > button * {
            color: #0284c7 !important;
            font-weight: 700 !important;
            font-size: 0.88rem !important;
        }
        div[data-testid="stButton"] > button:hover {
            background: #0284c7 !important;
            border-color: #0284c7 !important;
            box-shadow: 0 0 10px rgba(2, 132, 199, 0.3) !important;
        }
        div[data-testid="stButton"] > button:hover * {
            color: #ffffff !important;
        }

        .kpi-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 18px 22px;
            text-align: left;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
            transition: all 0.25s ease;
        }
        .kpi-card:hover {
            border-color: #0284c7;
            transform: translateY(-3px);
            box-shadow: 0 6px 18px rgba(2, 132, 199, 0.12);
        }
        .kpi-label {
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #64748b;
            margin-bottom: 6px;
        }
        .kpi-value {
            font-family: 'Outfit', sans-serif;
            font-size: 2rem;
            font-weight: 800;
            color: #0f172a;
        }

        .news-card-container {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
        }
        .news-card-container:hover {
            transform: translateY(-4px);
            border-color: #0284c7;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        }
        
        .news-card-alt {
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
        .badge-alt-category {
            background: linear-gradient(135deg, #d946ef 0%, #db2777 100%) !important;
            color: #ffffff !important;
            padding: 5px 14px !important;
            border-radius: 8px !important;
            font-size: 0.8rem !important;
            font-weight: 800 !important;
            box-shadow: 0 2px 8px rgba(219, 39, 119, 0.3) !important;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-tone-opportunity {
            background: #dcfce7;
            border: 1px solid #86efac;
            color: #15803d;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-tone-alert {
            background: #fee2e2;
            border: 1px solid #fca5a5;
            color: #b91c1c;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
            margin-right: 8px;
        }
        .badge-tone-neutral {
            background: #fef3c7;
            border: 1px solid #fde68a;
            color: #b45309;
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
            color: #0f172a;
            text-decoration: none;
            margin-top: 12px;
            margin-bottom: 10px;
            display: block;
            transition: color 0.2s ease;
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

        .disclaimer-card {
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 14px;
            padding: 24px;
            margin-top: 40px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
        }
    </style>
    """, unsafe_allow_html=True)

# Header Principal Hero con Fechas Visibles
today_date_str = datetime.now().strftime("%d/%m/%Y")
last_update_str = st.session_state["last_updated"]

st.markdown(f"""
<div class="hero-header">
    <div>
        <div class="hero-title">⚡ Terminal Financiero & Feed de Noticias</div>
        <div class="hero-subtitle">Inteligencia de Mercado en Tiempo Real • Funds People • Funds Society • EFPA España • <b style="color: #db2777;">FONDOS ALTERNATIVOS</b></div>
    </div>
    <div class="hero-dates-box">
        <div class="hero-date-item">
            <span class="hero-date-label">📅 Fecha Actual</span>
            <span class="hero-date-val">{today_date_str}</span>
        </div>
        <div style="width: 1px; background: rgba(128,128,128,0.25); margin: 0 4px;"></div>
        <div class="hero-date-item">
            <span class="hero-date-label">⏱️ Última Actualización</span>
            <span class="hero-date-val">{last_update_str}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Mostrar toast si acaba de sincronizar
if st.session_state["just_synced"]:
    st.toast("⚡ Noticias en vivo resincronizadas con éxito desde las webs oficiales", icon="📰")
    st.success("Noticias en vivo resincronizadas con éxito desde las webs oficiales.")
    st.session_state["just_synced"] = False

# Función para cargar y sincronizar noticias en vivo reales con protección total contra fallos
def load_and_sync_data(force_sync: bool = False):
    enricher = AIEnricher()
    existing_news = []
    
    try:
        existing_news = db.get_all_news()
    except Exception as e:
        print(f"[App] Error leyendo base de datos: {e}")
        existing_news = []
    
    if not existing_news or force_sync:
        try:
            if force_sync:
                db.clear_all_news()
                
            raw_news = fetch_live_news()
            try:
                reader = GmailNewsletterReader()
                email_news = reader.fetch_today_emails()
                if email_news:
                    raw_news.extend(email_news)
            except Exception as e_email:
                print(f"[App] Error leyendo newsletters por email: {e_email}")
                
            enriched = [enricher.enrich_item(item) for item in raw_news]
            db.save_news_items(enriched)
            existing_news = db.get_all_news()
            st.session_state["last_updated"] = datetime.now().strftime("%H:%M:%S")
        except Exception as e_sync:
            print(f"[App] Excepción en sincronización en vivo, usando respaldo: {e_sync}")
            from backend.scraper import SEED_NEWS
            existing_news = SEED_NEWS
            
    return existing_news, enricher


# Botón de Sincronización en Vivo Reales
if st.sidebar.button("🔄 Sincronizar Noticias en Vivo", use_container_width=True, type="primary"):
    with st.spinner("Scrapeando titulares en vivo de FundsPeople, FundsSociety y procesando con Gemini 3.6 Flash..."):
        news_data, enricher = load_and_sync_data(force_sync=True)
        st.session_state["just_synced"] = True
        st.rerun()
else:
    news_data, enricher = load_and_sync_data(force_sync=False)

search_term = st.sidebar.text_input("🔍 Búsqueda global", placeholder="ej. RIS, Family Office, Bankinter, Private Equity...")

sources = ["Todas"] + sorted(list(set(item["source"] for item in news_data if item.get("source"))))
selected_source = st.sidebar.selectbox("🏛️ Fuente de noticias", sources)

categories = ["Todas", "FONDOS ALTERNATIVOS"] + [c for c in sorted(list(set(item["category"] for item in news_data if item.get("category")))) if c != "FONDOS ALTERNATIVOS"]
selected_category = st.sidebar.selectbox("🏷️ Categoría temática", categories)

sentiment_options = ["Todos", "Oportunidad", "Alerta Regulatoria", "Neutro"]
selected_sentiment = st.sidebar.selectbox("📊 Tono de Mercado", sentiment_options)

st.sidebar.markdown("---")

# Indicador de estado de la IA
ai_status_color = "#10b981" if enricher.client else "#f59e0b"
ai_status_text = "🟢 Gemini 3.6 Flash Activo" if enricher.client else "🟡 Modo Heurístico"

sidebar_card_bg = "rgba(15, 23, 42, 0.9)" if is_dark else "#f1f5f9"
sidebar_card_border = "rgba(255,255,255,0.12)" if is_dark else "#cbd5e1"
sidebar_title_color = "#ffffff" if is_dark else "#0f172a"

st.sidebar.markdown(f"""
<div style="background: {sidebar_card_bg}; border: 1px solid {sidebar_card_border}; border-radius: 10px; padding: 14px; margin-bottom: 15px;">
    <div style="font-size: 0.8rem; color: {sidebar_title_color}; font-weight: 700; text-transform: uppercase;">🤖 Inteligencia Artificial</div>
    <div style="font-size: 0.9rem; color: {ai_status_color}; font-weight: 700; margin-top: 4px;">{ai_status_text}</div>
    <div style="font-size: 0.82rem; color: #0284c7; margin-top: 8px;">💾 BD SQLite: <b>{len(news_data)} noticias activas</b></div>
</div>
""", unsafe_allow_html=True)

# Widget de Créditos en Sidebar
st.sidebar.markdown(f"""
<div style="background: {sidebar_card_bg}; border: 1px solid {sidebar_card_border}; border-radius: 10px; padding: 14px;">
    <div style="font-size: 0.75rem; color: #64748b; font-weight: 700; text-transform: uppercase;">👨‍💻 Creado por</div>
    <div style="font-size: 0.88rem; color: {sidebar_title_color}; font-weight: 700; margin-top: 2px;">Raúl Martín</div>
    <div style="font-size: 0.78rem; color: #0ea5e9; font-weight: 600;">Dpto. Banca Privada</div>
</div>
""", unsafe_allow_html=True)

# KPIs con Estilo Executive
col_k1, col_k2, col_k3, col_k4 = st.columns(4)
with col_k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Noticias Totales Hoy</div>
        <div class="kpi-value">{len(news_data)}</div>
    </div>
    """, unsafe_allow_html=True)
with col_k2:
    alt_funds_count = sum(1 for item in news_data if item.get("category") == "FONDOS ALTERNATIVOS")
    st.markdown(f"""
    <div class="kpi-card" style="border-color: {'rgba(236, 72, 153, 0.4)' if is_dark else '#f472b6'};">
        <div class="kpi-label" style="color: #db2777;">Fondos Alternativos ⚡</div>
        <div class="kpi-value" style="color: #ec4899;">{alt_funds_count}</div>
    </div>
    """, unsafe_allow_html=True)
with col_k3:
    fav_count = len(st.session_state["favorites"])
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Mis Favoritos ⭐</div>
        <div class="kpi-value" style="color: #d97706;">{fav_count}</div>
    </div>
    """, unsafe_allow_html=True)
with col_k4:
    sources_count = len(set(item["source"] for item in news_data if item.get("source")))
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Fuentes Activas 🌐</div>
        <div class="kpi-value" style="color: #0284c7;">{sources_count}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Hashtags de Tendencias
st.markdown("##### 🔥 Tendencias & Módulos Clave:")
tag_cols = st.columns(6)
all_tags = ["Todos", "#FondosAlternativos", "#FamilyOffice", "#PrivateEquity", "#NormativaRIS", "#TecnologiaIA"]
for i, tag in enumerate(all_tags):
    if tag_cols[i].button(tag, key=f"btn_tag_{i}", use_container_width=True):
        st.session_state["selected_tag"] = tag

# Pestañas Principales
tab_feed, tab_chat, tab_favorites, tab_digest = st.tabs([
    "📰 Feed de Noticias", 
    "🤖 Pregunta a tu Feed (Chat RAG)", 
    "⭐ Mis Favoritos", 
    "📝 Generar Digest Diario"
])

# Aplicar Filtros y Garantizar Unicidad de IDs
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

# Función para renderizar tarjeta de noticia con key única por pestaña
def render_impeccable_card(item: dict, key_prefix: str = "feed"):
    is_alt = item.get("category") == "FONDOS ALTERNATIVOS"
    card_class = "news-card-container news-card-alt" if is_alt else "news-card-container"
    category_badge_class = "badge-alt-category" if is_alt else "badge-category"
    
    sentiment = item.get("sentiment", "Neutro")
    if sentiment == "Oportunidad":
        tone_badge_class = "badge-tone-opportunity"
    elif sentiment == "Alerta Regulatoria":
        tone_badge_class = "badge-tone-alert"
    else:
        tone_badge_class = "badge-tone-neutral"
        
    is_fav = item["id"] in st.session_state["favorites"]
    fav_icon = "⭐ Guardada" if is_fav else "☆ Guardar"

    c_card, c_action = st.columns([0.88, 0.12])
    with c_card:
        hashtags_display = ' '.join(item.get('hashtags', [])) if isinstance(item.get('hashtags'), list) else ""
        action_btn_style = "text-decoration: none; font-weight: 700; color: #38bdf8; font-size: 0.88rem; background: rgba(56, 189, 248, 0.1); padding: 6px 14px; border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.2);" if is_dark else "text-decoration: none; font-weight: 700; color: #0284c7; font-size: 0.88rem; background: #e0f2fe; padding: 6px 14px; border-radius: 8px; border: 1px solid #7dd3fc;"
        tag_color = "#38bdf8" if is_dark else "#0284c7"
        date_color = "#94a3b8" if is_dark else "#64748b"
        
        st.markdown(f"""
        <div class="{card_class}">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span class="badge-source">🌐 {item.get('source', 'Fuente')}</span>
                    <span class="{category_badge_class}">⚡ {item.get('category', 'General')}</span>
                    <span class="{tone_badge_class}">{item.get('sentiment_badge', '🟡 Neutro')}</span>
                </div>
                <span style="color: {date_color}; font-size: 0.82rem; font-weight: 600;">📅 {item.get('date', '')}</span>
            </div>
            <a href="{item.get('url', '#')}" target="_blank" class="news-title-link">{item.get('title', '')}</a>
            <div class="news-summary-text">{item.get('summary', '')}</div>
            <div style="margin-top: 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <span style="font-size: 0.82rem; color: {tag_color}; font-weight: 600;">{hashtags_display}</span>
                <a href="{item.get('url', '#')}" target="_blank" style="{action_btn_style}">Leer artículo original en {item.get('source', 'fuente')} ↗</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c_action:
        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
        if st.button(fav_icon, key=f"{key_prefix}_fav_{item['id']}"):
            db.toggle_favorite(item["id"])
            st.session_state["favorites"] = db.get_favorites()
            st.rerun()

# Pestaña 1: Feed de Noticias
with tab_feed:
    if st.session_state["selected_tag"] != "Todos":
        st.info(f"Filtro por hashtag activo: **{st.session_state['selected_tag']}**")
        
    if not filtered_news:
        if search_term:
            st.warning(f"No hay noticias archivadas en el feed local que contengan la palabra **'{search_term}'**.")
            st.info(f"💡 **Tip**: La Búsqueda Global filtra sobre las noticias del día guardadas en la base de datos local. Si buscas análisis sobre un tema externo (como *'{search_term}'*), utiliza el asistente **🤖 Pregunta a tu Feed (Chat RAG)**.")
        else:
            st.warning("No se encontraron noticias que coincidan con los filtros aplicados.")
    else:
        for item in filtered_news:
            render_impeccable_card(item, key_prefix="feed")

# Pestaña 2: Chat RAG
with tab_chat:
    st.markdown("### 🤖 Asistente de Inteligencia sobre el Feed")
    st.caption("Respuesta contextual inmediata basada en el feed diario analizado por Google Gemini 3.6 Flash.")
    
    # Sugerencias rápidas
    st.markdown("**💡 Consultas sugeridas:**")
    q_col1, q_col2, q_col3 = st.columns(3)
    quick_query = None
    with q_col1:
        if st.button("⚡ Fondos Alternativos & PE", use_container_width=True, key="quick_alt"):
            quick_query = "¿Cuáles son las principales novedades y oportunidades en Fondos Alternativos y Mercados Privados hoy?"
    with q_col2:
        if st.button("⚖️ Novedades Normativas RIS", use_container_width=True, key="quick_reg"):
            quick_query = "¿Qué novedades normativas, regulación o alertas regulatorias destacan en el feed?"
    with q_col3:
        if st.button("🏛️ Movimientos Banca Privada", use_container_width=True, key="quick_pb"):
            quick_query = "¿Qué fichajes, entidades o movimientos estratégicos se mencionan en Banca Privada?"

    # Formulario de entrada (permite pulsar Enter o hacer clic)
    with st.form(key="chat_rag_form", clear_on_submit=True):
        f_col1, f_col2 = st.columns([5, 1])
        with f_col1:
            form_query = st.text_input(
                "Pregunta al asistente:",
                placeholder="Escribe tu consulta y pulsa Enter (ej. ¿Qué impacto tiene la directiva RIS?)...",
                label_visibility="collapsed"
            )
        with f_col2:
            submit_btn = st.form_submit_button("🚀 Consultar", type="primary", use_container_width=True)

    query_to_process = None
    if quick_query:
        query_to_process = quick_query
    elif submit_btn and form_query.strip():
        query_to_process = form_query.strip()

    if query_to_process:
        with st.spinner("Procesando consulta con Google Gemini 3.6 Flash..."):
            answer = enricher.ask_feed(query_to_process, news_data)
            st.session_state["chat_history"].append({"user": query_to_process, "assistant": answer, "time": datetime.now().strftime("%H:%M")})

    # Mostrar historial de conversación
    if st.session_state["chat_history"]:
        st.markdown("---")
        h_col1, h_col2 = st.columns([5, 1])
        with h_col1:
            st.markdown("#### 💬 Conversación")
        with h_col2:
            if st.button("🗑️ Limpiar Chat", use_container_width=True, key="clear_chat_btn"):
                st.session_state["chat_history"] = []
                st.rerun()

        for idx, chat in enumerate(reversed(st.session_state["chat_history"])):
            with st.chat_message("user"):
                st.markdown(f"**{chat['user']}** <span style='font-size:0.75rem; opacity:0.6;'>({chat.get('time', '')})</span>", unsafe_allow_html=True)
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(chat["assistant"])
    else:
        st.info("💡 Haz una pregunta en el recuadro superior o pulsa cualquiera de las consultas sugeridas para comenzar.")

# Pestaña 3: Mis Favoritos
with tab_favorites:
    st.markdown("### ⭐ Guardados para Lectura Posterior")
    fav_items = [item for item in news_data if item["id"] in st.session_state["favorites"]]
    if not fav_items:
        st.info("No has guardado noticias aún. Utiliza el botón '☆ Guardar' en cualquier tarjeta del Feed.")
    else:
        for item in fav_items:
            render_impeccable_card(item, key_prefix="favtab")

# Pestaña 4: Generar Digest
with tab_digest:
    st.markdown("### 📝 Generador de Digest Diario")
    st.caption("Compila y descarga el resumen ejecutivo diario listo para distribuir a clientes o equipo.")
    
    if st.button("✨ Generar Nuevo Digest con Gemini"):
        with st.spinner("Redactando informe ejecutivo con Gemini 3.6 Flash..."):
            st.session_state["digest_text"] = enricher.generate_daily_digest(news_data)
            
    digest_text = st.session_state.get("digest_text", enricher.generate_daily_digest(news_data))
    
    digest_bg = "#0f172a" if is_dark else "#ffffff"
    digest_border = "rgba(56, 189, 248, 0.35)" if is_dark else "#cbd5e1"
    digest_shadow = "rgba(0,0,0,0.5)" if is_dark else "rgba(0,0,0,0.06)"
    
    st.markdown(f"""
    <div style="background-color: {digest_bg}; border: 1px solid {digest_border}; border-radius: 14px; padding: 28px; margin-top: 15px; margin-bottom: 20px; box-shadow: 0 8px 30px {digest_shadow};">
    """, unsafe_allow_html=True)
    
    st.markdown(digest_text)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.download_button(
        label="📥 Descargar Digest en Markdown (.md)",
        data=digest_text,
        file_name=f"Digest_Financiero_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown"
    )

# --- DISCLAIMER Y CRÉDITOS TÉCNICOS ---
st.markdown("<br><hr style='border-color: rgba(128,128,128,0.2);'>", unsafe_allow_html=True)
with st.expander("ℹ️ Acerca de esta herramienta, Metodología, LLM y Créditos"):
    st.markdown("""
    ### ⚡ Terminal Financiero & Feed de Inteligencia de Mercado

    **👨‍💻 Creador & Autor:**  
    **Raúl Martín** — *Dpto. Banca Privada (Banco Mediolanum)*

    ---

    #### 🏗️ ¿Cómo se ha desarrollado esta aplicación?
    - **Arquitectura:** Aplicación interactiva de alto rendimiento desarrollada en **Python** sobre el framework **Streamlit**, diseñada con un sistema visual adaptable (*Dark Executive Glassmorphism* y *Light Executive Mode*).
    - **Almacenamiento:** Base de datos relacional persistente **SQLite (`news_feed.db`)** que almacena el histórico diario, favoritos y metadatos de clasificación.
    - **Extracción de Datos:** Scraping web y agregación RSS en tiempo real (mediante `httpx`, `BeautifulSoup4` y `feedparser`) sobre las principales cabeceras del sector financiero:
      - *Funds People* (incluyendo sección especializada *Alterforum*)
      - *Funds Society*
      - *EFPA España*
      - *Citywire*

    ---

    #### 🤖 Modelos de Inteligencia Artificial (LLM) Utilizados
    - **Modelo Principal:** **`Google Gemini 3.6 Flash`** (con fallback de alta disponibilidad a **`Gemini 3.5 Flash`**) integrado mediante el SDK oficial de última generación `google-genai`.
    - **Capacidades de IA:**
      1. **Clasificación Taxonómica y Detección de Sentimiento:** Categorización automática en nichos (*FONDOS ALTERNATIVOS, Banca Privada, Mercados Privados, Normativa & Regulaciones, Tecnología & IA*) y evaluación del tono de mercado (*🟢 Oportunidad, 🔴 Alerta Regulatoria, 🟡 Neutro*).
      2. **Asistente Conversacional RAG (Retrieval-Augmented Generation):** Motor de búsqueda semántica y contextual en la pestaña *Pregunta a tu Feed* para responder dudas específicas de asesores con citas directas.
      3. **Generador de Digest Ejecutivo:** Síntesis y redacción estructurada en Markdown del pulso del mercado diario.

    ---

    #### ⚖️ Disclaimer Legal
    *Esta herramienta ha sido creada como soporte de inteligencia de mercado y productividad interna para asesores de Banca Privada. Toda la información, titulares y enlaces pertenecen a sus respectivas fuentes editoriales de origen.*
    """)



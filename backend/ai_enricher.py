import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class AIEnricher:
    """
    Enriquece noticias mediante la API de Google Gemini (google-genai SDK) o reglas avanzadas de fallback:
    - Categorización (incluyendo FONDOS ALTERNATIVOS)
    - Tono / Sentimiento de Mercado (Oportunidad, Neutro, Alerta Regulatoria)
    - Chat RAG real sobre la colección de noticias
    - Generador de Digest Diario
    """
    def __init__(self, api_key: Optional[str] = None):
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY", "")
            if not api_key:
                try:
                    import streamlit as st
                    api_key = st.secrets.get("GEMINI_API_KEY", "")
                except Exception:
                    api_key = ""
        self.api_key = api_key
        self.client = None
        self.preferred_models = ["gemini-3.6-flash", "gemini-3.5-flash"]
        if GENAI_AVAILABLE and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[AIEnricher] Error al inicializar cliente Gemini: {e}")
                self.client = None

    def _generate(self, contents: str, config: Optional[Any] = None) -> Optional[str]:
        """Intenta generar contenido probando secuencialmente los modelos disponibles."""
        if not self.client:
            return None
        for model_name in self.preferred_models:
            try:
                if config:
                    resp = self.client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=config
                    )
                else:
                    resp = self.client.models.generate_content(
                        model=model_name,
                        contents=contents
                    )
                if resp and resp.text:
                    return resp.text
            except Exception as e:
                print(f"[AIEnricher] Intento con {model_name} falló: {e}")
        return None

    def enrich_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Garantiza que la noticia tenga categorización, tono de mercado y resumen enriquecido.
        Optimizado para omitir llamadas a Gemini si la noticia ya está enriquecida.
        """
        url = item.get("url", "")
        title = item.get("title", "")
        summary = item.get("summary", "")
        source = item.get("source", "")
        
        # Categoría especial Alterforum -> FONDOS ALTERNATIVOS siempre garantizada
        if "alterforum" in url.lower() or "alterforum" in title.lower() or "alterforum" in source.lower():
            item["category"] = "FONDOS ALTERNATIVOS"

        # Si ya cuenta con hashtags, sentimiento y categoría completos, retornar inmediatamente (evita llamadas API innecesarias)
        if item.get("category") and item.get("sentiment") and item.get("hashtags") and len(item.get("hashtags", [])) > 0:
            return item

        # Intentar enriquecimiento rápido con Gemini para noticias nuevas sin clasificar
        if self.client:
            try:
                prompt = f"""Analiza la siguiente noticia de banca privada / finanzas:
Título: {title}
Fuente: {source}
URL: {url}
Resumen/Texto: {summary}

Responde exclusivamente en formato JSON válido con la siguiente estructura:
{{
  "category": "FONDOS ALTERNATIVOS | Banca Privada | Mercados Privados | Normativa & Regulaciones | Tecnología & IA | Gestión Patrimonial",
  "sentiment": "Oportunidad | Alerta Regulatoria | Neutro",
  "sentiment_badge": "🟢 Oportunidad | 🔴 Alerta | 🟡 Neutro",
  "summary": "Resumen ejecutivo en 2-3 viñetas concisas",
  "hashtags": ["#Hashtag1", "#Hashtag2"]
}}"""
                gen_text = self._generate(
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2
                    )
                )
                if gen_text:
                    data = json.loads(gen_text)
                    if item.get("category") != "FONDOS ALTERNATIVOS":
                        item["category"] = data.get("category", item.get("category", "Banca Privada"))
                    item["sentiment"] = data.get("sentiment", "Neutro")
                    item["sentiment_badge"] = data.get("sentiment_badge", "🟡 Neutro")
                    if data.get("summary"):
                        item["summary"] = data["summary"]
                    item["hashtags"] = data.get("hashtags", ["#BancaPrivada"])
                    return item
            except Exception as e:
                print(f"[AIEnricher] Fallback heurístico en enrich_item: {e}")

        # --- FALLBACK HEURÍSTICO ULTRARRÁPIDO ---
        if not item.get("category"):
            if any(w in title.lower() or w in summary.lower() for w in ["ley", "ris", "normativa", "regulación", "incentivos"]):
                item["category"] = "Normativa & Regulaciones"
            elif any(w in title.lower() or w in summary.lower() for w in ["ia", "inteligencia", "tecnología", "agéntica"]):
                item["category"] = "Tecnología & IA"
            elif any(w in title.lower() or w in summary.lower() for w in ["private equity", "mercados privados", "inmobiliario"]):
                item["category"] = "Mercados Privados"
            else:
                item["category"] = "Banca Privada"
                
        if not item.get("sentiment"):
            if any(w in title.lower() or w in summary.lower() for w in ["ris", "regulación", "normativa", "requisitos", "desafíos", "retrocesiones"]):
                item["sentiment"] = "Alerta Regulatoria"
                item["sentiment_badge"] = "🔴 Alerta"
            elif any(w in title.lower() or w in summary.lower() for w in ["lanza", "supera", "unifica", "crecimiento", "oportunidad", "nueva"]):
                item["sentiment"] = "Oportunidad"
                item["sentiment_badge"] = "🟢 Oportunidad"
            else:
                item["sentiment"] = "Neutro"
                item["sentiment_badge"] = "🟡 Neutro"
            
        hashtags = item.get("hashtags", [])
        if not hashtags:
            if item["category"] == "FONDOS ALTERNATIVOS":
                hashtags.append("#FondosAlternativos")
            if "private" in title.lower() or "equity" in title.lower():
                hashtags.append("#PrivateEquity")
            if "family" in title.lower() or "wealth" in title.lower():
                hashtags.append("#FamilyOffice")
            if "ris" in title.lower() or "normativa" in title.lower():
                hashtags.append("#NormativaRIS")
            if "ia" in title.lower() or "inteligencia" in title.lower():
                hashtags.append("#TecnologiaIA")
                
            if not hashtags:
                hashtags.append("#BancaPrivada")
            
        item["hashtags"] = hashtags
        return item

    def ask_feed(self, query: str, news_items: List[Dict[str, Any]]) -> str:
        """
        Responde a consultas sobre el feed de noticias utilizando Gemini RAG o fallback heurístico.
        """
        if self.client and news_items:
            try:
                context_str = ""
                for idx, item in enumerate(news_items[:25], 1):
                    context_str += f"\n[{idx}] Título: {item['title']}\nFuente: {item['source']}\nCategoría: {item['category']}\nURL: {item['url']}\nResumen: {item['summary']}\n"
                
                prompt = f"""Eres un analista de banca privada experto de Banco Mediolanum. 
Responde a la siguiente consulta del usuario apoyándote en la colección de noticias financieras proporcionada.
Si la información no aparece en las noticias, indícalo cortésmente y ofrece contexto general relacionado con el mercado financiero.
Incluye enlaces markdown a las fuentes de las noticias mencionadas siempre que sea posible.

Noticias Disponibles:
{context_str}

Pregunta del Asesor: {query}"""

                gen_text = self._generate(contents=prompt)
                if gen_text:
                    return gen_text
            except Exception as e:
                print(f"[AIEnricher] Fallback RAG por error Gemini: {e}")

        # Fallback RAG básico
        query_lower = query.lower()
        matching_items = []
        for item in news_items:
            combined = f"{item['title']} {item['summary']} {item['category']} {item['source']}".lower()
            if any(term in combined for term in query_lower.split()):
                matching_items.append(item)
                
        if not matching_items:
            matching_items = news_items[:3]
            
        response = f"### 💡 Análisis del Feed para: *\"{query}\"*\n\n"
        response += f"He encontrado **{len(matching_items)} noticias relevantes** en las fuentes del día:\n\n"
        
        for idx, item in enumerate(matching_items[:4], 1):
            response += f"**{idx}. [{item['title']}]({item['url']})**\n"
            response += f"- **Fuente:** {item['source']} | **Categoría:** `{item['category']}` | **Tono:** {item.get('sentiment_badge', '🟡 Neutro')}\n"
            response += f"- **Resumen:** {item['summary']}\n\n"
            
        response += "---\n*Respuesta generada a partir del feed diario de Banco Mediolanum.*"
        return response

    def generate_daily_digest(self, news_items: List[Dict[str, Any]]) -> str:
        """
        Genera un resumen diario maquetado en Markdown listo para compartir con clientes o equipo.
        """
        today_str = datetime.now().strftime("%d de %B de %Y")
        
        if self.client and news_items:
            try:
                context_str = json.dumps([{
                    "title": i["title"], 
                    "source": i["source"], 
                    "category": i["category"], 
                    "summary": i["summary"], 
                    "url": i["url"]
                } for i in news_items[:10]], ensure_ascii=False)

                prompt = f"""Genera un Informe Ejecutivo de Noticias Financieras en formato Markdown profesional para un Asesor de Banca Privada en Banco Mediolanum.
Fecha: {today_str}
Noticias a resumir:
{context_str}

Estructura requerida:
# 📑 RESUMEN DIARIO DE NOTICIAS FINANCIERAS
**Fecha:** {today_str}
**Fuentes Integradas:** FundsPeople, FundsSociety, EFPA España & Alterforum

## 🎯 CLAVES Y TENDENCIAS DEL DÍA (Visión Sintética)
## ⚡ ESPECIAL FONDOS ALTERNATIVOS & MERCADOS PRIVADOS
## 💡 IMPLICACIONES PARA CLIENTES DE BANCA PRIVADA BANCO MEDIOLANUM
"""
                gen_text = self._generate(contents=prompt)
                if gen_text:
                    return gen_text
            except Exception as e:
                print(f"[AIEnricher] Fallback Digest por error Gemini: {e}")

        # Fallback Template Digest
        alt_funds = [item for item in news_items if item.get("category") == "FONDOS ALTERNATIVOS"]
        other_news = [item for item in news_items if item.get("category") != "FONDOS ALTERNATIVOS"]
        
        digest = f"""# 📑 RESUMEN DIARIO DE NOTICIAS FINANCIERAS
**Fecha:** {today_str}
**Fuentes Integradas:** FundsPeople, FundsSociety, EFPA España & Alterforum

---

## 🎯 NOTICIAS DESTACADAS
"""
        for item in other_news[:5]:
            clean_summary = item['summary'].replace('\n', ' ')
            digest += f"• **{item['title']}** ({item['source']})\n  {clean_summary}\n  🔗 [Leer noticia original]({item['url']})\n\n"
            
        if alt_funds:
            digest += "## ⚡ ESPECIAL FONDOS ALTERNATIVOS (ALTERFORUM)\n"
            for item in alt_funds:
                clean_summary = item['summary'].replace('\n', ' ')
                digest += f"• **{item['title']}**\n  {clean_summary}\n  🔗 [Ver en Alterforum]({item['url']})\n\n"
                
        digest += """---
*Generado automáticamente por el Feed Financiero Inteligente de Banco Mediolanum.*
"""
        return digest

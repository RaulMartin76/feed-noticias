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
    Enriquece noticias especializadas en Inteligencia Artificial y Robótica para consultoría tecnológica:
    - Categorización (ROBÓTICA & EMBODIED AI, Modelos & LLMs, Hardware & Chips, Software & Agentes, Negocio & Consultoría, Regulación & Ética)
    - Tono de Mercado / Impacto Tecnológico (Innovación, Oportunidad, Alerta, Tendencia, Actualización)
    - Síntesis y traducción ejecutiva al español orientada a consultores
    - Asistente RAG interactivo para consultas estratégicas de IA
    - Generador de Morning AI Briefing diario
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
        self.preferred_models = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-2.5-flash", "gemini-flash-latest"]
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
        Garantiza que la noticia tenga categorización, impacto tecnológico y resumen enriquecido en español.
        """
        title = item.get("title", "")
        summary = item.get("summary", "")
        source = item.get("source", "")
        url = item.get("url", "")
        
        # Si ya cuenta con hashtags y resumen completo en español estructurado, retornar de inmediato
        if item.get("category") and item.get("sentiment") and item.get("hashtags") and len(item.get("hashtags", [])) > 0:
            return item

        # Intento de enriquecimiento con Gemini
        if self.client:
            try:
                prompt = f"""Eres el Analista Principal de Inteligencia Artificial y Robótica en una consultora tecnológica de primer nivel.
Analiza la siguiente noticia tecnológica:
Título: {title}
Fuente: {source}
URL: {url}
Texto/Resumen original: {summary}

Tu tarea:
1. Traduce y sintetiza en español en 2 viñetas concisas ("• ..."), explicando el avance técnico y su impacto práctico para clientes o proyectos de consultoría.
2. Clasifica en una de estas categorías exactas:
   - ROBÓTICA & EMBODIED AI (para humanoides, robótica industrial, drones autónomos, manipulación física)
   - Modelos & LLMs (para modelos de lenguaje, visión, razonamiento, benchmarks, open weights)
   - Hardware & Chips (para NVIDIA, GPUs, TPUs, semiconductores, centros de datos, refrigeración)
   - Software & Agentes (para frameworks de agentes, MCP, LangChain, librerías, inferencia local)
   - Negocio & Consultoría (para rondas de inversión, startups, adopción enterprise, M&A)
   - Regulación & Ética (para EU AI Act, propiedad intelectual, seguridad, gobernanza algorítmica)
3. Selecciona el tono: "Innovación" | "Oportunidad" | "Alerta" | "Tendencia" | "Actualización"
4. Badge visual: "🚀 Innovación" | "🚀 Oportunidad" | "⚠️ Alerta" | "📊 Tendencia" | "⚙️ Actualización" | "🦾 Robótica"
5. Asigna 2-3 hashtags (#Robótica, #LLMs, #HardwareNVIDIA, #AgentesIA, #OpenSource, #EUAIAct, #EnterpriseAI, #EmbodiedAI).

Responde exclusivamente con un JSON válido con esta estructura:
{{
  "category": "ROBÓTICA & EMBODIED AI | Modelos & LLMs | Hardware & Chips | Software & Agentes | Negocio & Consultoría | Regulación & Ética",
  "sentiment": "Innovación | Oportunidad | Alerta | Tendencia | Actualización",
  "sentiment_badge": "🚀 Innovación | 🚀 Oportunidad | ⚠️ Alerta | 📊 Tendencia | ⚙️ Actualización | 🦾 Robótica",
  "summary": "• Viñeta 1 en español\n• Viñeta 2 en español",
  "hashtags": ["#Tag1", "#Tag2"]
}}"""
                gen_text = self._generate(contents=prompt)
                if gen_text:
                    clean_json = gen_text.strip()
                    if "```json" in clean_json:
                        clean_json = clean_json.split("```json")[1].split("```")[0].strip()
                    elif "```" in clean_json:
                        clean_json = clean_json.split("```")[1].split("```")[0].strip()
                    data = json.loads(clean_json)
                    
                    item["category"] = data.get("category", item.get("category", "Modelos & LLMs"))
                    item["sentiment"] = data.get("sentiment", "Innovación")
                    item["sentiment_badge"] = data.get("sentiment_badge", "🚀 Innovación")
                    item["summary"] = data.get("summary", summary)
                    item["hashtags"] = data.get("hashtags", ["#InteligenciaArtificial"])
                    return item
            except Exception as e:
                print(f"[AIEnricher] Fallback a heurística de IA por error de API: {e}")

        # Fallback Heurístico Robusto Especializado en IA y Robótica
        return self._heuristic_enrichment(item)

    def _heuristic_enrichment(self, item: Dict[str, Any]) -> Dict[str, Any]:
        text = (item.get("title", "") + " " + item.get("summary", "")).lower()
        
        # Categorización
        if any(w in text for w in ["robot", "humanoid", "boston dynamics", "figure 0", "bipedal", "manipulation", "embodied", "actuator"]):
            category = "ROBÓTICA & EMBODIED AI"
            sentiment = "Innovación"
            sentiment_badge = "🦾 Robótica"
            hashtags = ["#Robótica", "#EmbodiedAI"]
        elif any(w in text for w in ["nvidia", "chip", "semiconductor", "blackwell", "tpu", "gpu", "tsmc", "quantum", "datacenter"]):
            category = "Hardware & Chips"
            sentiment = "Tendencia"
            sentiment_badge = "📊 Tendencia"
            hashtags = ["#HardwareNVIDIA", "#Semiconductores"]
        elif any(w in text for w in ["regulation", "act", "law", "copyright", "policy", "safety", "governance", "eu ai"]):
            category = "Regulación & Ética"
            sentiment = "Alerta"
            sentiment_badge = "⚠️ Alerta"
            hashtags = ["#EUAIAct", "#Gobernanza"]
        elif any(w in text for w in ["funding", "startup", "invest", "venture", "market", "acquisition", "enterprise", "consulting"]):
            category = "Negocio & Consultoría"
            sentiment = "Oportunidad"
            sentiment_badge = "🚀 Oportunidad"
            hashtags = ["#ConsultoríaIA", "#EnterpriseAI"]
        elif any(w in text for w in ["framework", "agent", "mcp", "library", "langchain", "open source", "python"]):
            category = "Software & Agentes"
            sentiment = "Actualización"
            sentiment_badge = "⚙️ Actualización"
            hashtags = ["#AgentesIA", "#SoftwareEnterprise"]
        else:
            category = "Modelos & LLMs"
            sentiment = "Innovación"
            sentiment_badge = "🚀 Innovación"
            hashtags = ["#LLMs", "#InteligenciaArtificial"]

        item["category"] = category
        item["sentiment"] = sentiment
        item["sentiment_badge"] = sentiment_badge
        item["hashtags"] = hashtags
        
        # Garantizar viñetas en el resumen
        summary = item.get("summary", "")
        if not summary.startswith("•"):
            item["summary"] = f"• {summary}"
            
        return item

    def ask_feed(self, query: str, news_items: List[Dict[str, Any]]) -> str:
        """
        Asistente RAG para el equipo de consultoría de IA: evalúa noticias, modelos y arquitecturas.
        """
        if self.client and news_items:
            try:
                context_str = ""
                for idx, item in enumerate(news_items[:25], 1):
                    context_str += f"\n[{idx}] Título: {item['title']}\nFuente: {item['source']}\nCategoría: {item['category']}\nURL: {item['url']}\nResumen: {item['summary']}\n"
                
                prompt = f"""Eres el Lead Architect y Director de Consultoría de Inteligencia Artificial y Robótica.
Responde a la consulta del consultor apoyándote rigurosamente en la colección de noticias tecnológicas del feed diario.
Ofrece recomendaciones técnicas, comparativas de modelos, consideraciones de despliegue en clientes o impacto en hardware/robótica.
Incluye enlaces markdown a las fuentes de las noticias citadas siempre que sea posible.

Noticias Tecnológicas Disponibles:
{context_str}

Pregunta del Consultor: {query}"""

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
            
        response = f"### 💡 Análisis del Feed de IA & Robótica para: *'{query}'*\n\n"
        response += f"He seleccionado **{len(matching_items)} novedades clave** relacionadas:\n\n"
        
        for idx, item in enumerate(matching_items[:4], 1):
            response += f"**{idx}. [{item['title']}]({item['url']})**\n"
            response += f"- **Fuente:** {item['source']} | **Categoría:** `{item['category']}` | **Impacto:** {item.get('sentiment_badge', '🚀 Innovación')}\n"
            response += f"- **Resumen:** {item['summary']}\n\n"
            
        response += "---\n*Respuesta generada para el equipo de Consultoría de Inteligencia Artificial & Robótica.*"
        return response

    def generate_daily_digest(self, news_items: List[Dict[str, Any]]) -> str:
        """
        Genera un Morning AI Briefing diario maquetado en Markdown listo para compartir con el equipo de consultoría.
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
                } for i in news_items[:12]], ensure_ascii=False)

                prompt = f"""Genera un Morning AI Briefing de Inteligencia Artificial y Robótica en formato Markdown para una Consultoría Tecnológica.
Fecha: {today_str}
Noticias a compilar:
{context_str}

Estructura requerida:
# ⚡ MORNING AI & ROBOTICS BRIEFING
**Fecha:** {today_str}
**Fuentes Integradas:** TechCrunch AI, The Verge, MIT Tech Review, MarkTechPost, IEEE Spectrum, The Robot Report & Hugging Face

## 🎯 TOP HEADLINES & MODELOS FUNDACIONALES
(Síntesis de los avances más relevantes en LLMs, arquitecturas y Big Tech)

## 🦾 ESPECIAL ROBÓTICA & EMBODIED AI
(Análisis de novedades en robots humanoides, visión-acción y automatización física)

## 💻 HARDWARE, INFRAESTRUCTURA & CHIPS
(Novedades en semiconductores, centros de datos y eficiencia de cómputo)

## 💡 RECOMENDACIONES ESTRATÉGICAS PARA CLIENTES DE CONSULTORÍA
(Puntos de acción concretos para asesorar a empresas y proyectos en curso)
"""
                gen_text = self._generate(contents=prompt)
                if gen_text:
                    return gen_text
            except Exception as e:
                print(f"[AIEnricher] Fallback Digest por error Gemini: {e}")

        # Fallback Template Digest
        robotics_news = [item for item in news_items if item.get("category") == "ROBÓTICA & EMBODIED AI"]
        other_news = [item for item in news_items if item.get("category") != "ROBÓTICA & EMBODIED AI"]
        
        digest = f"""# ⚡ MORNING AI & ROBOTICS BRIEFING
**Fecha:** {today_str}
**Fuentes Integradas:** TechCrunch AI, The Verge, MIT Tech Review, MarkTechPost, IEEE Spectrum, The Robot Report & Hugging Face

---

## 🎯 NOTICIAS DESTACADAS EN INTELIGENCIA ARTIFICIAL
"""
        for item in other_news[:5]:
            clean_summary = item['summary'].replace('\n', ' ')
            digest += f"• **{item['title']}** ({item['source']})\n  {clean_summary}\n  🔗 [Leer noticia original]({item['url']})\n\n"
            
        if robotics_news:
            digest += "## 🦾 ESPECIAL ROBÓTICA & EMBODIED AI\n"
            for item in robotics_news:
                clean_summary = item['summary'].replace('\n', ' ')
                digest += f"• **{item['title']}** ({item['source']})\n  {clean_summary}\n  🔗 [Ver artículo original]({item['url']})\n\n"
                
        digest += """## 💡 RECOMENDACIONES PARA CLIENTES DE CONSULTORÍA
• **Evaluación de Modelos:** Priorizar arquitecturas de razonamiento híbrido para tareas con alta exigencia de precisión.
• **Gobernanza:** Asegurar trazabilidad de datos y cumplimiento con directrices de auditoría algorítmica.
• **Infraestructura:** Optimizar costes de inferencia mediante cuantización y modelos específicos para casos de uso verticales.

---
*Compilado automáticamente para el equipo de Consultoría de IA y Robótica.*
"""
        return digest

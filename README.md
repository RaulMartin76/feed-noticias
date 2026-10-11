# 🤖 Terminal IA & Robótica • Feed de Inteligencia Tecnológica

> **Plataforma de Inteligencia de Mercado en Tiempo Real para Consultoría de Inteligencia Artificial y Robótica**

---

## 📌 Visión General

El **Terminal IA & Robótica** es una solución automatizada diseñada para monitorear, categorizar y enriquecer las novedades diarias de vanguardia tecnológica publicadas a nivel global:

- 🚀 **TechCrunch AI**
- 📰 **The Verge AI**
- 🔬 **MIT Technology Review**
- ⚡ **MarkTechPost (AI Research & Frameworks)**
- 🦾 **IEEE Spectrum (Robotics)**
- 🦾 **The Robot Report (Industrial & Humanoid Robotics)**
- 🤗 **Hugging Face Blog**
- 🌐 **Wired AI**

La plataforma integra inteligencia artificial (**Google Gemini AI**) para sintetizar cada noticia en viñetas ejecutivas en español, asignar impacto tecnológico, responder consultas técnicas de consultoría (*Chat RAG sobre el Feed*) y redactar el informe diario (*Morning AI Briefing*).

---

## 🔥 Funcionalidades Clave

1. **Rastreo Global en Vivo**: Extracción directa de titulares y resúmenes de los principales centros de noticias de IA y robótica mundiales.
2. **Especial Robótica & Embodied AI**: Módulo destacado para seguimiento prioritario de humanoides (Figure, Boston Dynamics, Tesla Optimus), visión-acción y automatización física.
3. **🤖 Asistente de Consultoría (Chat RAG)**: Analista virtual impulsado por Gemini AI que responde dudas técnicas, comparativas de modelos y frameworks (MCP, LangGraph) y normativas (EU AI Act).
4. **📝 Generador de Morning AI Briefing**: Compilación instantánea de resúmenes ejecutivos diarios descargables en `.md`.
5. **⭐ Artículos Guardados**: Persistencia en base de datos local SQLite para lectura y preparación de propuestas a clientes.
6. **🎨 Interfaz Cyber Dark & Tech Light**: Diseño de alta legibilidad optimizado para entornos de ingeniería y consultoría.

---

## 💻 Ejecución Local

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar la Clave de Gemini AI**:
   Crea un archivo `.env` en la raíz con tu clave API de Gemini:
   ```env
   GEMINI_API_KEY=tu_api_key_aqui
   ```

3. **Lanzar la Aplicación**:
   ```bash
   streamlit run frontend/app.py
   ```

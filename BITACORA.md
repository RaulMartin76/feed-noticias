# 📋 BITÁCORA DE CONTROL • VADEMECUM HUB NEWS
**Fecha de registro:** 11 de Octubre de 2026  
**Proyecto:** Vademecum Hub News & Intelligence (Radar IA + Reddit + Discord + Newsletter)  
**Rama activa:** `feed-ia` en `Feed noticias IA`  
**Repositorio GitHub:** [github.com/RaulMartin76/feed-noticias](https://github.com/RaulMartin76/feed-noticias) (Rama `feed-ia`)  

---

## 1. 🏗️ Arquitectura de Repositorios (Aislamiento Garantizado)

Para proteger el feed financiero original y no causar regresiones:
* **Entorno 1 (Financiero):** `c:\Users\marti\Downloads\PROYECTOS\CANALES\Feed noticias`  
  * **Rama:** `main` | **Puerto Local:** `http://localhost:8501`  
  * **Estado:** 100% intacto, fuentes bancarias originales (`Funds Society`, `Funds People`, `EFPA`, etc.).
* **Entorno 2 (IA & Vademecum Hub):** `c:\Users\marti\Downloads\PROYECTOS\CANALES\Feed noticias IA`  
  * **Rama:** `feed-ia` | **Puerto Local:** `http://localhost:8502`  
  * **Estado:** Desarrollado, verificado empíricamente y sincronizado con GitHub.

---

## 2. 🚀 Funcionalidades Implementadas y Verificadas

### A. Diseño Corporativo Oficial Vademecum Hub
* **Paleta de Colores:** Fondo obsidiana `#0e0d0c`, marfil `#f4efe6`, oro envejecido `#c9a227` / `#f59e0b`, y acentos teal `#2f6f6a`.
* **Modo Luz Corporativo:** Barra lateral izquierda en **Azul Marino Intenso** (`#071527` a `#0c2340`) con tipografías en blanco puro y oro de alto contraste.
* **Selector de Tema:** Reubicado en la esquina superior derecha (`🌙 Oscuro` / `☀️ Luz`) para no saturar la barra lateral.
* **Barra Horizontal de Pestañas:** Rediseñada tipo cápsulas (*pills*); la pestaña activa resalta de forma visible (dorado en oscuro, azul marino en claro).

### B. Canales de Información Integrados
1. **Radar de Novedades IA:** Rastreando en vivo portales de tecnología y clasificado por Gemini AI.
2. **Pulso de Reddit IA:** 100% real en tiempo real vía RSS/JSON público (`r/LocalLLaMA`, `r/MachineLearning`, `r/Singularity`, etc.).
3. **Pulso de Discord:** Estructura modular preparada con canales de servidores de IA (modo seed/mock a la espera de Bot Token).
4. **Saneamiento HTML:** Resueltas fugas de etiquetas `<a href...>` y `>a ref...` generadas por inyección de Markdown.

### C. Lanzador de Newsletter para Clientes
* **Base de Datos Supabase:** Adaptado al esquema oficial de Vademecum (`public.leads`: `nombre`, `email`, `empresa`, `tipo`).
* **Plantilla de Email Corporativa:** Generador HTML responsive para clientes ejecutivos con llamada a la acción (*CTA*).
* **Motor Resend:** Conector por API HTTP con clave de entorno.
* **Protección MVP con Confirmación:** Al hacer clic en enviar a clientes, se activa un diálogo de confirmación obligatorio (`✅ Sí, Confirmar y Enviar` / `❌ Cancelar`) para prevenir despachos accidentales.
* **Acceso Lateral:** Tarjeta de estado y selector de acceso rápido directamente en la barra izquierda.

---

## 3. 🔑 Estado de Credenciales y Servicios

| Servicio | Estado | Detalle |
| :--- | :--- | :--- |
| **Google Gemini API** | 🟢 **Activo** | Clasificación, resumen y chat RAG funcional. |
| **Resend API** | 🟢 **Validado** | Clave `re_G6i8z...` con permisos de envío verificados en servidor. |
| **Supabase DB** | 🟡 **Fallback Seguro** | Clave `sb_publishable_...` configurada. El subdominio `owkawzkmfnxjftosdvkz` está pausado en Supabase por inactividad. La app muestra 8 clientes simulados para evitar bloqueos. |
| **Reddit** | 🟢 **En vivo** | Consulta pública sin requerir login personal. |
| **Discord** | ⚪ **Pendiente Token** | Requiere crear Bot de Discord si se desean mensajes de servidores propios. |

---

## 4. 📦 Historial de Commits en GitHub (`feed-ia`)

```
b107f1b - feat(ui): barra lateral azul intenso en modo luz, selector de tema superior, pestanas contrastadas y confirmacion en envio de newsletter
716cb77 - feat(newsletter): anadir selector de modo Resend en vivo y soporte de remitente personalizable
2304b5e - feat(newsletter): soporte explicito de claves supabase y manejo resiliente de fallback
fb2e0fd - feat(newsletter): anadir modulo de servicio y pestana de newsletter en frontend con simulador Resend y Supabase
e14330a - feat(discord-clean): eliminar fugas de codigo HTML e integrar lector de canales Discord
41fba72 - feat(reddit): anadir modulo de rastreo y resumen de debates de IA en Reddit
0dfc618 - feat(vademecum): adaptar identidad visual, paleta corporativa y tipografia Outfit/Plus Jakarta Sans
4003eb7 - feat(ia-feed): inicializar entorno independiente para radar de IA y Robotica
```

---

## 5. 🎯 Próximos Pasos para Mañana

1. **Reanudar Supabase:** Entrar a [supabase.com/dashboard](https://supabase.com/dashboard) y hacer clic en *"Restore Project"* para conectar la tabla `leads` real.
2. **Dominio Corporativo en Resend:** Si se desea enviar desde `noticias@vademecumhub.com` en lugar de `onboarding@resend.dev`.
3. **Bot de Discord (Opcional):** Si quieres volcar discusiones reales de tus servidores privados de Discord.
4. **Despliegue en la Nube:** Preparar contenedor Docker / Cloudflare Tunnel para acceso remoto seguro HTTPS.

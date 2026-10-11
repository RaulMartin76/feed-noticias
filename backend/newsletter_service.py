import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()

TODAY_STR = datetime.now().strftime("%d de %B de %Y")

# Base de datos simulada de clientes de consultoría (esquema idéntico a public.leads de Supabase)
SIMULATED_LEADS: List[Dict[str, Any]] = [
    {
        "id": "lead-1",
        "nombre": "Carlos Mendoza",
        "email": "carlos.mendoza@innovabanking.com",
        "empresa": "Innova Banking",
        "tipo": "consultoria",
        "estado": "activo"
    },
    {
        "id": "lead-2",
        "nombre": "Elena Rivas",
        "email": "elena.rivas@logisticsai.es",
        "empresa": "Logistics AI Hub",
        "tipo": "consultoria",
        "estado": "activo"
    },
    {
        "id": "lead-3",
        "nombre": "Alejandro Gómez",
        "email": "agomez@retailfuture.io",
        "empresa": "Retail Future",
        "tipo": "consultoria",
        "estado": "activo"
    },
    {
        "id": "lead-4",
        "nombre": "Lucía Morales",
        "email": "lmorales@pharmahealth.com",
        "empresa": "Pharma Health Corp",
        "tipo": "formacion",
        "estado": "activo"
    },
    {
        "id": "lead-5",
        "nombre": "Javier Sanz",
        "email": "javier.sanz@automotive-robotics.eu",
        "empresa": "Automotive Robotics",
        "tipo": "consultoria",
        "estado": "activo"
    },
    {
        "id": "lead-6",
        "nombre": "Marta Domínguez",
        "email": "marta.d@legaltech-advisors.es",
        "empresa": "LegalTech Advisors",
        "tipo": "consultoria",
        "estado": "activo"
    },
    {
        "id": "lead-7",
        "nombre": "Santiago Peña",
        "email": "spena@fintech-ventures.com",
        "empresa": "Fintech Ventures",
        "tipo": "apps",
        "estado": "activo"
    },
    {
        "id": "lead-8",
        "nombre": "Beatriz Varela",
        "email": "bvarela@energy-grid.org",
        "empresa": "Energy Grid AI",
        "tipo": "consultoria",
        "estado": "activo"
    }
]

class NewsletterService:
    def __init__(self):
        self.supabase_url = os.environ.get("SUPABASE_URL", "")
        self.supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
        self.resend_api_key = os.environ.get("RESEND_API_KEY", "")
        self.sender_email = os.environ.get("NEWSLETTER_FROM_EMAIL", "Vademecum Hub News <newsletter@vademecumhub.com>")

    def is_simulator_mode(self) -> bool:
        """Determina si el servicio está en modo simulador (sin claves reales aún) o producción."""
        return not (bool(self.resend_api_key) and bool(self.supabase_url) and bool(self.supabase_key))

    def get_subscribers(self, tipo_filtro: str = "Todos") -> List[Dict[str, Any]]:
        """
        Obtiene los clientes registrados.
        Si hay credenciales de Supabase configuradas, consulta la tabla 'public.leads'.
        De lo contrario, utiliza los clientes simulados de Vademecum Hub.
        """
        subscribers = []
        
        if self.supabase_url and self.supabase_key:
            try:
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json"
                }
                url = f"{self.supabase_url.rstrip('/')}/rest/v1/leads?select=id,nombre,email,empresa,tipo,estado&consentimiento=eq.true"
                with httpx.Client(timeout=6.0) as client:
                    resp = client.get(url, headers=headers)
                    if resp.status_code == 200:
                        subscribers = resp.json()
                    else:
                        print(f"[Newsletter] Supabase devolvió código {resp.status_code}. Usando simulador.")
                        subscribers = SIMULATED_LEADS
            except Exception as e:
                print(f"[Newsletter] Error conectando a Supabase: {e}. Usando simulador.")
                subscribers = SIMULATED_LEADS
        else:
            subscribers = SIMULATED_LEADS

        # Filtrar por tipo si corresponde
        if tipo_filtro != "Todos":
            subscribers = [s for s in subscribers if s.get("tipo", "").lower() == tipo_filtro.lower()]

        return subscribers

    def generate_html_email(self, markdown_content: str, subject_title: str) -> str:
        """
        Transforma el informe Markdown en una plantilla HTML de email responsive de alto nivel,
        optimizada para Gmail, Apple Mail y Outlook con la estética Vademecum Hub.
        """
        html_body = markdown_content
        
        # Eliminar primer encabezado si ya está en el header
        html_body = re.sub(r'^#\s+.*?\n', '', html_body, flags=re.MULTILINE)
        
        # Convertir secciones H2
        html_body = re.sub(
            r'##\s+(.*?)\n', 
            r'<div style="margin-top: 26px; margin-bottom: 12px; border-bottom: 1px solid #2e2a24; padding-bottom: 6px;"><h2 style="color: #c9a227; font-size: 16px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin: 0;">\1</h2></div>', 
            html_body
        )
        
        # Convertir negritas
        html_body = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #f4efe6;">\1</strong>', html_body)
        
        # Convertir enlaces
        html_body = re.sub(
            r'\[(.*?)\]\((.*?)\)', 
            r'<a href="\2" target="_blank" style="color: #c9a227; text-decoration: none; font-weight: 600;">\1 &rarr;</a>', 
            html_body
        )
        
        # Convertir viñetas
        lines = html_body.split('\n')
        formatted_lines = []
        for line in lines:
            line_str = line.strip()
            if line_str.startswith('•') or line_str.startswith('*') or line_str.startswith('-'):
                clean_bullet = line_str.lstrip('•*- ')
                formatted_lines.append(f'<div style="margin-bottom: 10px; line-height: 1.6; color: #d6d0c4; font-size: 14px;"><span style="color: #c9a227; margin-right: 6px;">&bull;</span> {clean_bullet}</div>')
            elif line_str:
                formatted_lines.append(f'<p style="margin-bottom: 12px; line-height: 1.6; color: #a8a29e; font-size: 14px;">{line_str}</p>')
                
        content_html = '\n'.join(formatted_lines)

        full_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject_title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #080706; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f4efe6;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #080706; padding: 30px 10px;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="600" style="max-width: 600px; background-color: #12100d; border: 1px solid #2e2a24; border-radius: 14px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.6);">
                    
                    <!-- HEADER BRANDING VADEMECUM -->
                    <tr>
                        <td style="background: radial-gradient(ellipse 90% 80% at 50% -20%, rgba(201, 162, 39, 0.25), transparent 70%), #161411; border-bottom: 1px solid #2e2a24; padding: 30px 36px;">
                            <div style="font-size: 11px; color: #c9a227; font-weight: 800; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 6px;">
                                VADEMECUM HUB &bull; INTELLIGENCE BRIEFING
                            </div>
                            <h1 style="color: #f4efe6; font-size: 24px; font-weight: 800; margin: 0; letter-spacing: -0.02em;">
                                VADEMECUM HUB <span style="color: #c9a227;">NEWS</span>
                            </h1>
                            <div style="color: #a8a29e; font-size: 13px; margin-top: 6px;">
                                Radar Estratégico de Inteligencia Artificial &amp; Robótica para Clientes &bull; {TODAY_STR}
                            </div>
                        </td>
                    </tr>
                    
                    <!-- CUERPO PRINCIPAL -->
                    <tr>
                        <td style="padding: 32px 36px; background-color: #12100d;">
                            {content_html}
                        </td>
                    </tr>
                    
                    <!-- CALL TO ACTION CONSULTORÍA -->
                    <tr>
                        <td style="padding: 24px 36px; background-color: #181512; border-top: 1px solid #2e2a24; text-align: center;">
                            <div style="font-size: 14px; color: #f4efe6; font-weight: 700; margin-bottom: 8px;">
                                ¿Necesitas evaluar la integración de estas tecnologías en tu empresa?
                            </div>
                            <div style="font-size: 13px; color: #a8a29e; margin-bottom: 16px;">
                                Nuestro equipo de consultoría técnica diseña pruebas de concepto y estrategias a medida.
                            </div>
                            <a href="https://vademecumhub.com/consultoria" target="_blank" style="display: inline-block; background-color: #c9a227; color: #0e0d0c; font-weight: 800; font-size: 13px; padding: 10px 22px; border-radius: 8px; text-decoration: none;">
                                Agendar Sesión de Consultoría &rarr;
                            </a>
                        </td>
                    </tr>
                    
                    <!-- FOOTER CORPORATIVO -->
                    <tr>
                        <td style="padding: 24px 36px; background-color: #0e0d0c; border-top: 1px solid #24201b; text-align: center;">
                            <div style="font-size: 11px; color: #78716c; line-height: 1.5;">
                                Recibes este informe como cliente o suscriptor corporativo de <strong>Vademecum Hub</strong>.<br>
                                Vademecum Hub &bull; Consultoría y Soluciones Avanzadas de Inteligencia Artificial.<br>
                                <a href="https://vademecumhub.com" style="color: #a8a29e; text-decoration: underline;">vademecumhub.com</a> &bull; <a href="#" style="color: #78716c;">Preferencias de suscripción</a>
                            </div>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
        return full_template

    def send_newsletter(
        self, 
        recipients: List[Dict[str, Any]], 
        subject: str, 
        html_content: str,
        is_simulation: bool = True
    ) -> Dict[str, Any]:
        """
        Envía la newsletter a los destinatarios.
        - En modo Simulación: Simula la entrega con métricas y registros de prueba.
        - En modo Producción: Dispara la API de Resend para entrega real.
        """
        results = {
            "total": len(recipients),
            "sent": 0,
            "failed": 0,
            "errors": [],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": "Simulación (Mock)" if is_simulation else "Producción (Resend API)"
        }

        if is_simulation or not self.resend_api_key:
            for r in recipients:
                results["sent"] += 1
            return results

        # Modo producción real con Resend
        headers = {
            "Authorization": f"Bearer {self.resend_api_key}",
            "Content-Type": "application/json"
        }

        with httpx.Client(timeout=10.0) as client:
            for r in recipients:
                payload = {
                    "from": self.sender_email,
                    "to": [r["email"]],
                    "subject": subject,
                    "html": html_content
                }
                try:
                    resp = client.post("https://api.resend.com/emails", headers=headers, json=payload)
                    if resp.status_code in [200, 201]:
                        results["sent"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"{r['email']}: {resp.status_code} - {resp.text}")
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"{r['email']}: {str(e)}")

        return results

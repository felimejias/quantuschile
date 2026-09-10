"""
Quantus LinkedIn Channel
------------------------
Publica automaticamente en LinkedIn (pagina de empresa o perfil personal)
con dos vias de configuracion:

1. API oficial de LinkedIn (gratis; requiere aprobacion Community Management API):
   LINKEDIN_ACCESS_TOKEN -> token OAuth con scope w_organization_social o w_member_social
   LINKEDIN_AUTHOR_URN   -> "urn:li:organization:XXXX" o "urn:li:person:XXXX"
   LINKEDIN_API_VERSION  -> version de la API en formato YYYYMM (default 202604)

2. Zapier webhook (plan free: 100 tareas/mes):
   ZAPIER_LINKEDIN_WEBHOOK -> URL del zap "Webhook by Zapier" (Catch Hook).
   El JSON enviado incluye {text, url} para mapear en Zapier.

Si no hay configuracion, el canal queda en pending_config (no envia nada).
La API oficial tiene prioridad sobre el webhook si ambas estan configuradas.
"""

import os

import requests

LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_AUTHOR_URN = os.getenv("LINKEDIN_AUTHOR_URN", "")
LINKEDIN_API_VERSION = os.getenv("LINKEDIN_API_VERSION", "202604")
ZAPIER_LINKEDIN_WEBHOOK = os.getenv("ZAPIER_LINKEDIN_WEBHOOK", "")


def linkedin_configured():
    """True si hay alguna via configurada para publicar en LinkedIn."""
    return bool(_oficial_configured() or ZAPIER_LINKEDIN_WEBHOOK)


def _oficial_configured():
    return bool(LINKEDIN_ACCESS_TOKEN and LINKEDIN_AUTHOR_URN)


def _enviar_api_oficial(texto):
    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Linkedin-Version": LINKEDIN_API_VERSION,
        "Content-Type": "application/json",
    }
    payload = {
        "author": LINKEDIN_AUTHOR_URN,
        "commentary": texto,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    try:
        r = requests.post("https://api.linkedin.com/rest/posts", headers=headers, json=payload, timeout=30)
    except Exception as exc:
        return False, f"LinkedIn API: error de red ({str(exc)[:80]})"
    if r.status_code in (200, 201):
        urn = (r.headers.get("x-restli-id") or "").strip()
        return True, f"LinkedIn API: publicado {urn}" if urn else f"LinkedIn API: HTTP {r.status_code}"
    try:
        detalle = (r.json().get("message") or r.text)[:200]
    except Exception:
        detalle = r.text[:200]
    return False, f"LinkedIn API HTTP {r.status_code}: {detalle}"


def _enviar_webhook(texto, url=""):
    try:
        r = requests.post(ZAPIER_LINKEDIN_WEBHOOK, json={"text": texto, "url": url}, timeout=30)
    except Exception as exc:
        return False, f"Zapier webhook: error de red ({str(exc)[:80]})"
    if 200 <= r.status_code < 300:
        return True, f"Zapier webhook: HTTP {r.status_code}"
    return False, f"Zapier webhook HTTP {r.status_code}: {r.text[:200]}"


def send_linkedin(texto, url=""):
    """Publica en LinkedIn. Devuelve (ok, detalle).

    Sin configuracion devuelve (False, "linkedin_pending_config").
    """
    texto = (texto or "").strip()
    if not texto:
        return False, "texto vacio"
    if _oficial_configured():
        return _enviar_api_oficial(texto)
    if ZAPIER_LINKEDIN_WEBHOOK:
        return _enviar_webhook(texto, url)
    return False, "linkedin_pending_config"

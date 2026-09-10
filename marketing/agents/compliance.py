"""
Quantus Marketing Center — Agente de Cumplimiento.

Valida automáticamente el contenido de marketing contra:
1. Matriz de claims permitidos/bloqueados (claims_matrix.py)
2. Restricciones visuales (visual_restrictions.py)
3. URLs con UTM válidos (utm_builder.py)
4. Ortografía básica y marca corporativa
5. Presencia de identificación legal

Referencia: implementation_plan.md v2, §2 (Agente 4), §8, §16.

Normas:
- Ley 19.496 art. 28 (veracidad publicitaria)
- Ley 20.169 (competencia desleal)
- CARTA_MAGNA Reglas 17-19
"""

import json
import re
from datetime import datetime

from marketing.claims_matrix import check_text_compliance, DISCLAIMER_TEXT
from marketing.visual_restrictions import check_visual_prompt_compliance
from marketing.utm_builder import validate_utm_url


def run_compliance_check(content, service_category, assets=None):
    """
    Ejecuta todas las validaciones de cumplimiento sobre un contenido.

    Args:
        content: dict con al menos {body, channel, destination_url, title}
        service_category: Categoría del servicio
        assets: lista de dicts con {prompt_text} si hay activos visuales

    Returns:
        dict con:
            - overall_status: 'PASS', 'WARNING' o 'BLOCKED'
            - checks: lista de checks individuales
            - claims_validated: claims permitidos encontrados
            - claims_blocked: claims bloqueados encontrados
            - timestamp: fecha/hora de la verificación
    """
    checks = []
    claims_blocked = []
    claims_validated = []

    body = content.get("body", "")
    channel = content.get("channel", "")
    destination_url = content.get("destination_url", "")
    title = content.get("title", "")
    full_text = f"{title} {body}"

    # 1. Validación de claims (matriz)
    claims_result = check_text_compliance(full_text, service_category)
    checks.append({
        "check": "claims_matrix",
        "status": claims_result["status"],
        "details": claims_result["details"],
        "norm": "Ley 19.496 art. 28, Ley 20.169, CARTA_MAGNA Regla 17",
    })
    claims_blocked = claims_result["blocked_phrases"]

    # 2. Verificar identificación corporativa
    corp_check = _check_corporate_identity(full_text)
    checks.append(corp_check)

    # 3. Verificar URLs con UTM
    if destination_url:
        utm_check = _check_utm(destination_url)
        checks.append(utm_check)
    else:
        checks.append({
            "check": "utm_validation",
            "status": "WARNING",
            "details": ["No se proporcionó destination_url — no se puede verificar UTM"],
            "norm": "Regla interna Quantus (trazabilidad de campañas)",
        })

    # 4. Verificar disclaimer si menciona organismos
    if claims_result["needs_disclaimer"]:
        disclaimer_check = _check_disclaimer(full_text)
        checks.append(disclaimer_check)

    # 5. Verificaciones básicas de texto
    basic_checks = _check_basic_text_quality(full_text, channel)
    checks.extend(basic_checks)

    # 6. Validación visual (si hay assets)
    if assets:
        for asset in assets:
            prompt = asset.get("prompt_text", "")
            if prompt:
                visual_result = check_visual_prompt_compliance(prompt)
                checks.append({
                    "check": "visual_compliance",
                    "status": visual_result["status"],
                    "details": visual_result["details"],
                    "norm": "Ley 20.169, Ley 19.496 art. 28, CARTA_MAGNA Regla 17",
                })

    # Determinar status global
    statuses = [c["status"] for c in checks]
    if "BLOCKED" in statuses:
        overall_status = "BLOCKED"
    elif "WARNING" in statuses:
        overall_status = "WARNING"
    else:
        overall_status = "PASS"

    return {
        "overall_status": overall_status,
        "checks": checks,
        "claims_validated": claims_validated,
        "claims_blocked": claims_blocked,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }


def _check_corporate_identity(text):
    """Verifica presencia de identificación Quantus Chile SpA."""
    text_lower = text.lower()
    if "quantus chile spa" in text_lower or "quantus chile" in text_lower:
        return {
            "check": "corporate_identity",
            "status": "PASS",
            "details": ["Identificación corporativa presente"],
            "norm": "Ley 19.496 (identificación del proveedor)",
        }
    return {
        "check": "corporate_identity",
        "status": "WARNING",
        "details": ["No contiene 'Quantus Chile SpA' o 'Quantus Chile'"],
        "norm": "Ley 19.496 (identificación del proveedor)",
    }


def _check_utm(url):
    """Valida parámetros UTM en la URL."""
    result = validate_utm_url(url)
    if result["valid"]:
        return {
            "check": "utm_validation",
            "status": "PASS",
            "details": [f"UTM válido: {result['params']}"],
            "norm": "Regla interna Quantus (trazabilidad de campañas)",
        }
    return {
        "check": "utm_validation",
        "status": "WARNING",
        "details": [f"Parámetros UTM faltantes: {result['missing']}"],
        "norm": "Regla interna Quantus (trazabilidad de campañas)",
    }


def _check_disclaimer(text):
    """Verifica presencia del disclaimer de no afiliación."""
    if DISCLAIMER_TEXT.lower() in text.lower():
        return {
            "check": "disclaimer",
            "status": "PASS",
            "details": ["Disclaimer de no afiliación presente"],
            "norm": "Ley 20.169 (competencia desleal), MINIMO_WEB_CHILE.md §A5",
        }
    return {
        "check": "disclaimer",
        "status": "WARNING",
        "details": [
            "Menciona organismos públicos pero no incluye disclaimer de no afiliación. "
            f"Texto sugerido: '{DISCLAIMER_TEXT}'"
        ],
        "norm": "Ley 20.169 (competencia desleal), MINIMO_WEB_CHILE.md §A5",
    }


def _check_basic_text_quality(text, channel):
    """Verificaciones básicas de calidad del texto."""
    checks = []

    # Verificar largo mínimo
    if len(text.strip()) < 20:
        checks.append({
            "check": "text_length",
            "status": "WARNING",
            "details": ["Texto muy corto (< 20 caracteres)"],
            "norm": "Regla interna Quantus",
        })
    else:
        checks.append({
            "check": "text_length",
            "status": "PASS",
            "details": [f"Largo del texto: {len(text)} caracteres"],
            "norm": "Regla interna Quantus",
        })

    # Verificar que no haya URLs rotas (http sin https)
    if "http://" in text and "https://" not in text:
        checks.append({
            "check": "https_check",
            "status": "WARNING",
            "details": ["Contiene URL con http:// en vez de https://"],
            "norm": "Ley 21.663 (ciberseguridad), CARTA_MAGNA Regla 10",
        })

    # Verificar largo máximo por canal
    max_lengths = {
        "instagram": 2200,
        "linkedin": 3000,
        "facebook": 5000,
        "whatsapp_template": 1024,
        "whatsapp_status": 700,
    }
    max_len = max_lengths.get(channel)
    if max_len and len(text) > max_len:
        checks.append({
            "check": "channel_length_limit",
            "status": "WARNING",
            "details": [f"Texto excede el límite del canal {channel}: {len(text)}/{max_len}"],
            "norm": f"Política de plataforma ({channel})",
        })

    return checks

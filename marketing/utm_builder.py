"""
Quantus Marketing Center — Generador de URLs con UTM.

Genera URLs con parámetros de atribución UTM consistentes.
Referencia: implementation_plan.md v2, §14.
"""

from urllib.parse import urlencode, urlparse, urlunparse, parse_qs


# Base URL del sitio
BASE_URL = "https://quantuschile.cl"

# Mapeo de servicios a rutas
SERVICE_PATHS = {
    "diario_oficial": "/do",
    "licitaciones": "/licitaciones",
    "inapi": "/registro",
    "remates": "/remates-inmuebles-chile",
    "ley_21719": "/ley-21719",
    "erp": "/erp",
    "agentes_ia": "/como-funciona",
}

# Valores válidos para utm_medium
VALID_MEDIUMS = {"social", "direct", "email", "referral"}


def build_utm_url(
    service_category,
    channel,
    campaign_name,
    content_id=None,
    variant=None,
    custom_path=None,
):
    """
    Genera una URL con parámetros UTM completos.

    Args:
        service_category: Categoría del servicio ('diario_oficial', 'licitaciones', etc.)
        channel: Canal de origen ('instagram', 'facebook', 'linkedin', 'whatsapp', 'email')
        campaign_name: Nombre de la campaña (ej: 'diario_oficial_agosto_2026')
        content_id: UUID del contenido específico (opcional)
        variant: Variante A/B (opcional)
        custom_path: Ruta personalizada en vez de la del servicio (opcional)

    Returns:
        str: URL completa con parámetros UTM.
    """
    # Determinar la ruta
    path = custom_path or SERVICE_PATHS.get(service_category, "/")

    # Determinar utm_medium
    if channel in ("instagram", "facebook", "linkedin"):
        medium = "social"
    elif channel in ("whatsapp_template", "whatsapp_status", "whatsapp"):
        medium = "direct"
    elif channel == "email":
        medium = "email"
    else:
        medium = "referral"

    # Construir parámetros UTM
    params = {
        "utm_source": channel,
        "utm_medium": medium,
        "utm_campaign": _sanitize_campaign_name(campaign_name),
    }

    if content_id:
        params["utm_content"] = content_id

    if variant:
        params["utm_term"] = variant

    # Construir URL
    url = f"{BASE_URL}{path}?{urlencode(params)}"
    return url


def _sanitize_campaign_name(name):
    """Normaliza el nombre de campaña para UTM (lowercase, underscores, sin acentos)."""
    import unicodedata
    # Normalizar a ASCII
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = "".join(c for c in normalized if not unicodedata.combining(c))
    # Limpiar
    sanitized = ascii_name.lower().strip()
    sanitized = sanitized.replace(" ", "_").replace("-", "_")
    # Eliminar caracteres no alfanuméricos excepto underscore
    sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
    # Colapsar múltiples underscores
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")
    return sanitized.strip("_")


def validate_utm_url(url):
    """
    Valida que una URL contenga los parámetros UTM requeridos.

    Returns:
        dict con:
            - valid: bool
            - missing: lista de parámetros faltantes
            - params: dict de parámetros encontrados
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    required = ["utm_source", "utm_medium", "utm_campaign"]
    missing = [p for p in required if p not in params]

    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "params": {k: v[0] if len(v) == 1 else v for k, v in params.items()},
    }

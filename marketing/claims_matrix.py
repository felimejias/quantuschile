"""
Quantus Marketing Center — Matriz de Claims Autorizados y Bloqueados.

Define las afirmaciones permitidas y las prohibidas por servicio de Quantus.
El Agente de Cumplimiento valida cada texto contra esta matriz.
Referencia: implementation_plan.md v2, §8.

Normas de respaldo:
- Ley 19.496 art. 28 (publicidad engañosa) — /proyectos/NORMAS/CHILE/DFL3-19496_refundida.pdf
- Ley 20.169 (competencia desleal) — /proyectos/NORMAS/CHILE/Ley-20169_competencia_desleal.pdf
- CARTA_MAGNA.md Regla 17 (solo vender lo que funciona)
"""

# Frases UNIVERSALMENTE bloqueadas — en cualquier canal y cualquier servicio.
# Son patrones de texto que el Agente de Cumplimiento busca con coincidencia
# parcial (case-insensitive).
UNIVERSALLY_BLOCKED_PHRASES = [
    "100% garantizado",
    "100 % garantizado",
    "cien por ciento garantizado",
    "garantía total",
    "garantía absoluta",
    "perfecto",
    "sin errores",
    "sin fallos",
    "nunca falla",
    "infalible",
    "el mejor del mercado",
    "la mejor plataforma",
    "líder del mercado",
    "somos la plataforma oficial",
    "plataforma oficial de",
    "plataforma oficial del",
    "certificado por",
    "certificada por",
    "certificados por",
    "cumplimiento certificado",
    "aprobado por",
    "aprobada por",
    "avalado por",
    "avalada por",
    "respaldado por el gobierno",
    "respaldado por el estado",
    "seguridad absoluta",
    "seguridad total",
    "protección total",
    "protección absoluta",
    "reemplazamos a tu abogado",
    "reemplaza a tu abogado",
    "reemplaza a tu contador",
    "reemplazamos a tu contador",
    "reemplaza profesionales",
    "reemplaza a los profesionales",
    "la ia reemplaza",
    "no necesitas abogado",
    "no necesitas contador",
    "cumple automáticamente con la ley",
    "cumplimiento automático",
    "sin riesgo",
    "riesgo cero",
    "rentabilidad garantizada",
    "rentabilidad asegurada",
    "libre de riesgos",
]

# Claims por servicio: {servicio: {allowed: [...], blocked: [...]}}
# Las frases bloqueadas por servicio se suman a las universalmente bloqueadas.
SERVICE_CLAIMS = {
    "diario_oficial": {
        "allowed": [
            "Monitorea criterios configurados y alerta coincidencias",
            "Vigilancia automatizada del Diario Oficial",
            "Alerta cuando detecta menciones relevantes",
            "Búsqueda histórica en publicaciones oficiales",
            "Agentes de IA que revisan publicaciones diarias",
        ],
        "blocked": [
            "garantiza que detectará todas las publicaciones",
            "detecta el 100%",
            "no se le escapa nada",
            "cobertura total del diario oficial",
            "fuente oficial del diario oficial",
        ],
    },
    "licitaciones": {
        "allowed": [
            "Ayuda a encontrar oportunidades compatibles con tus criterios",
            "Monitoreo de licitaciones públicas",
            "Filtrado inteligente de oportunidades",
            "Alertas de nuevas licitaciones relevantes",
        ],
        "blocked": [
            "garantiza adjudicación",
            "asegura que ganarás",
            "te garantizamos contratos",
            "adjudicación garantizada",
            "ganarás licitaciones",
        ],
    },
    "inapi": {
        "allowed": [
            "Apoya el proceso de registro y monitorea coincidencias",
            "Búsqueda de marcas existentes",
            "Vigilancia de oposiciones",
            "Gestión del proceso de registro ante INAPI",
        ],
        "blocked": [
            "garantiza el registro de la marca",
            "tu marca será aprobada",
            "registro garantizado",
            "aprobación segura ante INAPI",
        ],
    },
    "remates": {
        "allowed": [
            "Centraliza y filtra oportunidades de remate público",
            "Información de remates judiciales disponibles",
            "Alertas de nuevos remates",
        ],
        "blocked": [
            "garantiza rentabilidad",
            "propiedad libre de riesgos",
            "inversión segura",
            "oportunidad sin riesgo",
            "rentabilidad asegurada",
        ],
    },
    "ley_21719": {
        "allowed": [
            "Ayuda a identificar brechas de preparación",
            "Herramientas para prepararse para la Ley 21.719",
            "Checklist de cumplimiento",
            "Diagnóstico de preparación",
        ],
        "blocked": [
            "certifica cumplimiento legal",
            "certificamos tu cumplimiento",
            "cumplimiento garantizado",
            "reemplaza asesoría jurídica",
            "no necesitas abogado",
            "cumplimiento automático de la ley",
        ],
    },
    "erp": {
        "allowed": [
            "Automatiza y centraliza procesos habilitados",
            "Gestión de inventario y ventas",
            "Control de clientes y operaciones",
            "Panel de administración empresarial",
        ],
        "blocked": [
            "elimina todos los errores",
            "cero errores",
            "sin errores operacionales",
            "perfecto para tu empresa",
            "sistema infalible",
        ],
    },
    "agentes_ia": {
        "allowed": [
            "Asiste y automatiza tareas configuradas",
            "Agentes de IA que procesan información",
            "Automatización inteligente",
            "Análisis asistido por IA",
        ],
        "blocked": [
            "reemplaza profesionales humanos",
            "la ia hace todo por ti",
            "no necesitas personal",
            "inteligencia artificial perfecta",
            "ia infalible",
        ],
    },
}

# Disclaimer obligatorio cuando se mencionan organismos públicos
DISCLAIMER_REQUIRED_WHEN_MENTIONING = [
    "diario oficial",
    "inapi",
    "mercado público",
    "chilecompra",
    "poder judicial",
    "sii",
    "servicio de impuestos internos",
    "sernac",
    "gobierno de chile",
]

DISCLAIMER_TEXT = (
    "Quantus Chile SpA es una plataforma privada y no representa ni mantiene "
    "afiliación oficial con los organismos mencionados."
)


def check_text_compliance(text, service_category):
    """
    Valida un texto contra la matriz de claims.

    Args:
        text: Texto a validar.
        service_category: Categoría del servicio ('diario_oficial', 'licitaciones', etc.)

    Returns:
        dict con:
            - status: 'PASS', 'WARNING' o 'BLOCKED'
            - blocked_phrases: lista de frases bloqueadas encontradas
            - needs_disclaimer: True si menciona organismos públicos
            - details: lista de mensajes detallados
    """
    text_lower = text.lower()
    blocked_found = []
    details = []
    needs_disclaimer = False

    # 1. Verificar frases universalmente bloqueadas
    for phrase in UNIVERSALLY_BLOCKED_PHRASES:
        if phrase.lower() in text_lower:
            blocked_found.append(phrase)
            details.append(
                f"BLOQUEADO — Frase universalmente prohibida: '{phrase}' "
                f"(Ley 19.496 art. 28, CARTA_MAGNA Regla 17)"
            )

    # 2. Verificar claims bloqueados por servicio
    service_rules = SERVICE_CLAIMS.get(service_category, {})
    for phrase in service_rules.get("blocked", []):
        if phrase.lower() in text_lower:
            blocked_found.append(phrase)
            details.append(
                f"BLOQUEADO — Claim prohibido para servicio '{service_category}': '{phrase}'"
            )

    # 3. Verificar si necesita disclaimer por mención de organismos
    for org in DISCLAIMER_REQUIRED_WHEN_MENTIONING:
        if org.lower() in text_lower:
            needs_disclaimer = True
            # Verificar si el disclaimer ya está incluido
            if DISCLAIMER_TEXT.lower() not in text_lower:
                details.append(
                    f"WARNING — Menciona '{org}' pero no incluye disclaimer de no afiliación"
                )

    # 4. Verificar que contenga identificación corporativa
    if "quantus chile spa" not in text_lower and "quantus chile" not in text_lower:
        details.append(
            "WARNING — No contiene identificación 'Quantus Chile SpA' o 'Quantus Chile'"
        )

    # Determinar status
    if blocked_found:
        status = "BLOCKED"
    elif needs_disclaimer and DISCLAIMER_TEXT.lower() not in text_lower:
        status = "WARNING"
    elif any("WARNING" in d for d in details):
        status = "WARNING"
    else:
        status = "PASS"

    return {
        "status": status,
        "blocked_phrases": blocked_found,
        "needs_disclaimer": needs_disclaimer,
        "details": details,
    }

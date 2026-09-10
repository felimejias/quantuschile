"""
Quantus Marketing Center — Restricciones del Agente Visual.

Define las prohibiciones de generación de imágenes.
Referencia: implementation_plan.md v2, §7.

Normas:
- Ley 19.496 art. 28 (publicidad engañosa)
- Ley 20.169 (competencia desleal, confusión, explotación de reputación ajena)
- CARTA_MAGNA Regla 17 (solo vender lo que funciona)
- Principio 3 de la Constitución Operativa (no inventar SVGs ni recreaciones)
"""

# Categorías de imágenes prohibidas con norma de respaldo
VISUAL_PROHIBITIONS = [
    {
        "category": "documentos_oficiales",
        "description": "Documentos oficiales del Estado (decretos, resoluciones, certificados)",
        "keywords": ["decreto", "resolución oficial", "certificado de", "acta oficial"],
        "norm": "Ley 20.169 (confusión), Ley 19.496 (engaño)",
    },
    {
        "category": "diario_oficial",
        "description": "Comunicaciones que simulen páginas del Diario Oficial",
        "keywords": ["diario oficial de la república", "publicación oficial"],
        "norm": "Ley 20.169",
    },
    {
        "category": "formularios_inapi",
        "description": "Formularios que parezcan solicitudes de marca ante INAPI",
        "keywords": ["formulario inapi", "solicitud de registro de marca"],
        "norm": "Ley 20.169",
    },
    {
        "category": "mercado_publico",
        "description": "Fichas de licitación o adjudicaciones de Mercado Público / ChileCompra",
        "keywords": ["ficha de licitación", "adjudicación oficial", "chilecompra"],
        "norm": "Ley 20.169",
    },
    {
        "category": "citaciones_judiciales",
        "description": "Notificaciones judiciales o citaciones legales",
        "keywords": ["citación judicial", "notificación del tribunal", "cédula de notificación"],
        "norm": "Ley 20.169, Código Penal",
    },
    {
        "category": "certificados_estatales",
        "description": "Certificados de nacimiento, antecedentes, tributarios u otros del Estado",
        "keywords": ["certificado de nacimiento", "certificado de antecedentes", "certificado tributario"],
        "norm": "Ley 20.169, Código Penal",
    },
    {
        "category": "sellos_cumplimiento",
        "description": "Sellos de cumplimiento inexistentes (Certificado ISO, Sello SERNAC, etc.)",
        "keywords": ["certificado iso", "sello sernac", "sello de cumplimiento", "sello oficial"],
        "norm": "Ley 19.496 art. 28 (engaño)",
    },
    {
        "category": "certificaciones_inexistentes",
        "description": "Certificaciones que Quantus no posee",
        "keywords": ["certificado en protección de datos", "certificación oficial"],
        "norm": "Ley 19.496 art. 28",
    },
    {
        "category": "logos_institucionales",
        "description": "Logos institucionales usados como patrocinio (Gobierno, Poder Judicial, SII)",
        "keywords": ["logo gobierno", "escudo nacional", "logo poder judicial", "logo sii"],
        "norm": "Ley 20.169 (explotación de reputación ajena), MINIMO_WEB_CHILE.md §A5",
    },
    {
        "category": "marcas_terceros",
        "description": "SVGs o recreaciones de marcas de terceros (RedCompra, WebPay, Mercado Pago, Gob.cl)",
        "keywords": ["redcompra", "webpay", "transbank", "mercado pago"],
        "norm": "CARTA_MAGNA Regla 17, Principio 3 (Constitución Operativa)",
    },
]

# Texto obligatorio en toda pieza visual generada
MANDATORY_BRANDING = "Quantus Chile SpA"

# Disclaimer para imágenes que referencian organismos
VISUAL_DISCLAIMER = (
    "Quantus Chile SpA es una plataforma privada y no representa ni mantiene "
    "afiliación oficial con los organismos mencionados."
)


def check_visual_prompt_compliance(prompt_text):
    """
    Valida un prompt de generación de imagen contra las restricciones.

    Args:
        prompt_text: Texto del prompt para generación de imagen.

    Returns:
        dict con:
            - status: 'PASS' o 'BLOCKED'
            - violations: lista de prohibiciones violadas
            - details: lista de mensajes
    """
    prompt_lower = prompt_text.lower()
    violations = []
    details = []

    for prohibition in VISUAL_PROHIBITIONS:
        for keyword in prohibition["keywords"]:
            if keyword.lower() in prompt_lower:
                violations.append({
                    "category": prohibition["category"],
                    "keyword": keyword,
                    "norm": prohibition["norm"],
                })
                details.append(
                    f"BLOQUEADO — Prompt contiene '{keyword}' que podría generar "
                    f"{prohibition['description']}. Norma: {prohibition['norm']}"
                )

    status = "BLOCKED" if violations else "PASS"
    return {
        "status": status,
        "violations": violations,
        "details": details,
    }

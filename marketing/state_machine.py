"""
Quantus Marketing Center — Máquina de estados canónica.

Define los 13 estados posibles, las transiciones permitidas y las prohibidas.
Referencia: implementation_plan.md v2, §11.
"""

# Estados canónicos
DRAFT = "DRAFT"
GENERATED = "GENERATED"
COMPLIANCE_REVIEW = "COMPLIANCE_REVIEW"
COMPLIANCE_BLOCKED = "COMPLIANCE_BLOCKED"
HUMAN_REVIEW = "HUMAN_REVIEW"
CHANGES_REQUESTED = "CHANGES_REQUESTED"
APPROVED = "APPROVED"
SCHEDULED = "SCHEDULED"
PUBLISHING = "PUBLISHING"
PUBLISHED = "PUBLISHED"
FAILED = "FAILED"
CANCELLED = "CANCELLED"
ARCHIVED = "ARCHIVED"

ALL_STATES = {
    DRAFT, GENERATED, COMPLIANCE_REVIEW, COMPLIANCE_BLOCKED,
    HUMAN_REVIEW, CHANGES_REQUESTED, APPROVED, SCHEDULED,
    PUBLISHING, PUBLISHED, FAILED, CANCELLED, ARCHIVED,
}

# Transiciones permitidas: {estado_actual: {estados_destino}}
ALLOWED_TRANSITIONS = {
    DRAFT: {GENERATED, CANCELLED},
    GENERATED: {COMPLIANCE_REVIEW, CANCELLED},
    COMPLIANCE_REVIEW: {COMPLIANCE_BLOCKED, HUMAN_REVIEW},
    COMPLIANCE_BLOCKED: {DRAFT},  # Editor corrige y vuelve a borrador
    HUMAN_REVIEW: {CHANGES_REQUESTED, APPROVED},
    CHANGES_REQUESTED: {DRAFT},  # Editor corrige
    APPROVED: {SCHEDULED},
    SCHEDULED: {PUBLISHING, CANCELLED},
    PUBLISHING: {PUBLISHED, FAILED},
    PUBLISHED: {ARCHIVED},
    FAILED: {SCHEDULED},  # Reintento registrado
    CANCELLED: {ARCHIVED},
    ARCHIVED: set(),  # Inmutable
}

# Transiciones explícitamente prohibidas con motivo
PROHIBITED_TRANSITIONS = {
    (DRAFT, PUBLISHED): "Salta todos los controles de cumplimiento y aprobación",
    (COMPLIANCE_BLOCKED, SCHEDULED): "No se puede programar contenido bloqueado por cumplimiento",
    (COMPLIANCE_BLOCKED, APPROVED): "No se puede aprobar sin resolver el bloqueo de cumplimiento",
    (CHANGES_REQUESTED, PUBLISHED): "No se puede publicar sin aplicar los cambios solicitados",
    (FAILED, PUBLISHED): "No se puede declarar publicado sin un nuevo intento exitoso registrado",
    (CANCELLED, PUBLISHING): "No se puede publicar contenido cancelado",
    (CANCELLED, PUBLISHED): "No se puede declarar publicado algo cancelado",
}


def can_transition(current_state, target_state):
    """
    Verifica si la transición es permitida.

    Returns:
        tuple: (bool, str|None) — (permitido, motivo_de_rechazo)
    """
    if current_state not in ALL_STATES:
        return False, f"Estado actual '{current_state}' no es válido"
    if target_state not in ALL_STATES:
        return False, f"Estado destino '{target_state}' no es válido"

    # Verificar prohibiciones explícitas
    key = (current_state, target_state)
    if key in PROHIBITED_TRANSITIONS:
        return False, PROHIBITED_TRANSITIONS[key]

    # Verificar transiciones permitidas
    allowed = ALLOWED_TRANSITIONS.get(current_state, set())
    if target_state in allowed:
        return True, None

    return False, f"Transición de '{current_state}' a '{target_state}' no está permitida"


def validate_transition(current_state, target_state):
    """
    Valida la transición y lanza ValueError si no es permitida.
    """
    allowed, reason = can_transition(current_state, target_state)
    if not allowed:
        raise ValueError(f"Transición prohibida: {current_state} → {target_state}. {reason}")
    return True

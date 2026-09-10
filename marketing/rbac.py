"""
Quantus Marketing Center — RBAC (Control de Acceso Basado en Roles).

Define 6 roles, permisos por operación y reglas de separación de funciones.
Referencia: implementation_plan.md v2, §10.
"""

# Roles
MARKETING_VIEWER = "MARKETING_VIEWER"
MARKETING_EDITOR = "MARKETING_EDITOR"
MARKETING_APPROVER = "MARKETING_APPROVER"
MARKETING_PUBLISHER = "MARKETING_PUBLISHER"
COMPLIANCE_REVIEWER = "COMPLIANCE_REVIEWER"
MARKETING_ADMIN = "MARKETING_ADMIN"

ALL_ROLES = {
    MARKETING_VIEWER,
    MARKETING_EDITOR,
    MARKETING_APPROVER,
    MARKETING_PUBLISHER,
    COMPLIANCE_REVIEWER,
    MARKETING_ADMIN,
}

# Permisos por operación
PERMISSIONS = {
    "view":     {MARKETING_VIEWER, MARKETING_EDITOR, MARKETING_APPROVER, MARKETING_PUBLISHER, COMPLIANCE_REVIEWER, MARKETING_ADMIN},
    "create":   {MARKETING_EDITOR, MARKETING_ADMIN},
    "edit":     {MARKETING_EDITOR, MARKETING_ADMIN},
    "approve":  {MARKETING_APPROVER, MARKETING_ADMIN},
    "publish":  {MARKETING_PUBLISHER, MARKETING_ADMIN},
    "schedule": {MARKETING_PUBLISHER, MARKETING_ADMIN},
    "compliance_review":  {COMPLIANCE_REVIEWER, MARKETING_ADMIN},
    "compliance_block":   {COMPLIANCE_REVIEWER, MARKETING_ADMIN},
    "compliance_unblock": {COMPLIANCE_REVIEWER, MARKETING_ADMIN},
    "cancel":   {MARKETING_EDITOR, MARKETING_APPROVER, MARKETING_PUBLISHER, MARKETING_ADMIN},
    "archive":  {MARKETING_ADMIN},
    "manage_suppressions": {COMPLIANCE_REVIEWER, MARKETING_ADMIN},
    "manage_leads": {MARKETING_EDITOR, MARKETING_APPROVER, MARKETING_ADMIN},
    "export":   {MARKETING_VIEWER, MARKETING_EDITOR, MARKETING_APPROVER, MARKETING_PUBLISHER, COMPLIANCE_REVIEWER, MARKETING_ADMIN},
}


def has_permission(role, operation):
    """Verifica si un rol tiene permiso para una operación."""
    if role not in ALL_ROLES:
        return False
    allowed_roles = PERMISSIONS.get(operation, set())
    return role in allowed_roles


def check_permission(role, operation):
    """Verifica permiso y lanza ValueError si no tiene acceso."""
    if not has_permission(role, operation):
        raise PermissionError(
            f"Rol '{role}' no tiene permiso para la operación '{operation}'"
        )
    return True


def can_approve_own_content(actor_id, content_created_by, role):
    """
    Regla de separación de funciones: un editor no puede aprobar su propio contenido.

    Returns:
        tuple: (bool, str|None) — (permitido, motivo_de_rechazo)
    """
    if role == MARKETING_ADMIN:
        # Admin puede aprobar cualquier contenido (pero se registra en auditoría)
        return True, None

    if actor_id == content_created_by:
        return False, "Un editor no puede aprobar su propio contenido (separación de funciones)"

    return True, None


def can_lift_compliance_block(role):
    """
    Solo COMPLIANCE_REVIEWER o MARKETING_ADMIN pueden levantar un bloqueo de cumplimiento.
    Un MARKETING_EDITOR no puede.
    """
    if role in {COMPLIANCE_REVIEWER, MARKETING_ADMIN}:
        return True, None
    return False, "Solo un COMPLIANCE_REVIEWER o MARKETING_ADMIN puede levantar un bloqueo de cumplimiento"


def validate_flow_b_permissions(role):
    """
    El Flujo B (directo/mensajería) requiere adicionalmente COMPLIANCE_REVIEWER
    para la primera publicación de cada plantilla nueva.
    """
    if role in {COMPLIANCE_REVIEWER, MARKETING_ADMIN}:
        return True, None
    return False, "El Flujo B requiere revisión de COMPLIANCE_REVIEWER para plantillas nuevas"


# Mapeo de rol por defecto para la sesión del maestro (propietario)
# En el MVP, el usuario autenticado como maestro tiene rol MARKETING_ADMIN
def get_role_for_session(session_data):
    """
    Determina el rol de marketing del usuario actual.
    En el MVP, el maestro autenticado es MARKETING_ADMIN.
    """
    if session_data.get("quantus_master_authenticated"):
        return MARKETING_ADMIN
    return None

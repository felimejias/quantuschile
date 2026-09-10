"""
Quantus Communications
----------------------
Capa reutilizable de comunicaciones con clientes:

- audit_log: historial auditable y anti-duplicado (dedup_key).
- dispatcher: despacho unificado de correo, WhatsApp y PDF.
- templates: plantillas por modulo y evento.

Primer consumidor: Radar Diario Oficial (diario_oficial).
Licitaciones, INAPI y Remates reutilizaran el mismo patron.
"""

from communications.audit_log import (  # noqa: F401
    already_sent,
    communications_snapshot,
    dedup_key_for,
    ensure_audit_storage,
    get_communication,
    list_communications,
    mark_communication_status,
    now_iso,
    record_communication,
)
from communications.dispatcher import dispatch, resend  # noqa: F401

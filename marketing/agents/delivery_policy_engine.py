"""
Quantus Marketing Center — Motor de Política de Entrega.

Ejecuta las 11 validaciones previas al envío para el Flujo B (mensajería directa).
Referencia: implementation_plan.md v2, §4.7.

Normativa actual aplicable:
- Ley 19.496 art. 28 B (derecho a solicitar cese de envíos)
- Ley 19.628 (finalidad del tratamiento)
- Políticas de Meta (opt-in obligatorio para WhatsApp Business Platform)
- Sistema No Molestar del SERNAC

Preparación:
- Ley 21.719 art. 8 ter (derecho de oposición a marketing directo) — vigencia 01-DIC-2026
"""

from datetime import datetime, timedelta

from marketing.db import get_db_conn, dict_from_row


# Resultados posibles
PASS = "DELIVERY_POLICY_PASS"
BLOCK = "DELIVERY_POLICY_BLOCK"


def evaluate_delivery(contact_id, channel, content_hash, campaign_id, tenant_id="quantus"):
    """
    Ejecuta las 11 validaciones previas al envío de un mensaje directo.

    Args:
        contact_id: ID del contacto destinatario
        channel: Canal de envío ('whatsapp', 'email')
        content_hash: Hash del contenido para deduplicación
        campaign_id: ID de la campaña
        tenant_id: ID del tenant

    Returns:
        dict con:
            - result: 'DELIVERY_POLICY_PASS' o 'DELIVERY_POLICY_BLOCK'
            - block_reason: código del bloqueo (None si PASS)
            - details: mensaje descriptivo
            - checks: lista de todas las verificaciones realizadas
    """
    checks = []
    conn = get_db_conn()
    try:
        # 1. ¿Tiene consentimiento activo para este canal?
        consent_check = _check_consent(conn, contact_id, channel, tenant_id)
        checks.append(consent_check)
        if consent_check["blocked"]:
            return _result(BLOCK, "NO_CONSENT", consent_check["detail"], checks)

        # 2. ¿Está en la lista de supresión?
        suppression_check = _check_suppression(conn, contact_id, channel, campaign_id, tenant_id)
        checks.append(suppression_check)
        if suppression_check["blocked"]:
            return _result(BLOCK, "SUPPRESSED", suppression_check["detail"], checks)

        # 3. ¿Superó el máximo diario para este canal?
        daily_check = _check_daily_limit(conn, contact_id, channel, tenant_id)
        checks.append(daily_check)
        if daily_check["blocked"]:
            return _result(BLOCK, "DAILY_LIMIT", daily_check["detail"], checks)

        # 4. ¿Superó el máximo semanal?
        weekly_check = _check_weekly_limit(conn, contact_id, channel, tenant_id)
        checks.append(weekly_check)
        if weekly_check["blocked"]:
            return _result(BLOCK, "WEEKLY_LIMIT", weekly_check["detail"], checks)

        # 5. ¿Está dentro del periodo de enfriamiento?
        cooldown_check = _check_cooldown(conn, contact_id, channel, tenant_id)
        checks.append(cooldown_check)
        if cooldown_check["blocked"]:
            return _result(BLOCK, "COOLDOWN", cooldown_check["detail"], checks)

        # 6. ¿Recibió el mismo contenido en los últimos N días?
        duplicate_check = _check_duplicate_content(conn, contact_id, channel, content_hash, tenant_id)
        checks.append(duplicate_check)
        if duplicate_check["blocked"]:
            return _result(BLOCK, "DUPLICATE_CONTENT", duplicate_check["detail"], checks)

        # 7. ¿Está en horario restringido?
        hours_check = _check_blocked_hours(conn, channel, tenant_id)
        checks.append(hours_check)
        if hours_check["blocked"]:
            return _result(BLOCK, "BLOCKED_HOURS", hours_check["detail"], checks)

        # 8. ¿Rechazó la misma campaña antes?
        rejected_check = _check_rejected_campaign(conn, contact_id, campaign_id)
        checks.append(rejected_check)
        if rejected_check["blocked"]:
            return _result(BLOCK, "REJECTED_CAMPAIGN", rejected_check["detail"], checks)

        # 9. ¿Tiene datos de contacto válidos?
        contact_check = _check_valid_contact(conn, contact_id, channel)
        checks.append(contact_check)
        if contact_check["blocked"]:
            return _result(BLOCK, "INVALID_CONTACT", contact_check["detail"], checks)

        # 10. ¿Pertenece a un segmento excluido?
        segment_check = _check_excluded_segment(conn, contact_id, campaign_id)
        checks.append(segment_check)
        if segment_check["blocked"]:
            return _result(BLOCK, "EXCLUDED_SEGMENT", segment_check["detail"], checks)

        # 11. ¿Está en el registro No Molestar del SERNAC?
        no_molestar_check = _check_no_molestar(conn, contact_id, tenant_id)
        checks.append(no_molestar_check)
        if no_molestar_check["blocked"]:
            return _result(BLOCK, "NO_MOLESTAR", no_molestar_check["detail"], checks)

        return _result(PASS, None, "Todas las verificaciones pasaron", checks)

    finally:
        conn.close()


def _result(result, reason, detail, checks):
    return {
        "result": result,
        "block_reason": reason,
        "details": detail,
        "checks": checks,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }


def _check_consent(conn, contact_id, channel, tenant_id):
    """Verificación 1: Consentimiento activo."""
    row = conn.execute(
        """SELECT id FROM marketing_consents
           WHERE contact_id = ? AND channel = ? AND tenant_id = ?
             AND consent_status = 'ACTIVE'
           LIMIT 1""",
        (contact_id, channel, tenant_id),
    ).fetchone()
    if row:
        return {"check": "consent", "blocked": False, "detail": "Consentimiento activo encontrado"}
    return {
        "check": "consent",
        "blocked": True,
        "detail": f"Sin consentimiento activo para canal '{channel}' "
                  f"(Política de Meta + Ley 19.628 + preparación Ley 21.719 art. 12)",
    }


def _check_suppression(conn, contact_id, channel, campaign_id, tenant_id):
    """Verificación 2: Lista de supresión."""
    row = conn.execute(
        """SELECT id, scope, reason FROM marketing_suppressions
           WHERE tenant_id = ? AND contact_id = ?
             AND (channel = ? OR channel = 'all')
             AND revoked_at IS NULL
             AND (expires_at IS NULL OR expires_at > ?)
           LIMIT 1""",
        (tenant_id, contact_id, channel, datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
    ).fetchone()
    if row:
        r = dict_from_row(row)
        return {
            "check": "suppression",
            "blocked": True,
            "detail": f"Contacto suprimido: scope={r['scope']}, reason={r['reason']} "
                      f"(Ley 19.496 art. 28 B)",
        }
    return {"check": "suppression", "blocked": False, "detail": "No está en lista de supresión"}


def _check_daily_limit(conn, contact_id, channel, tenant_id):
    """Verificación 3: Máximo diario."""
    policy = _get_policy(conn, channel, tenant_id)
    if not policy:
        return {"check": "daily_limit", "blocked": False, "detail": "Sin política de frecuencia configurada"}

    today = datetime.now().strftime("%Y-%m-%d")
    row = conn.execute(
        """SELECT COUNT(*) as cnt FROM marketing_delivery_log
           WHERE contact_id = ? AND channel = ? AND policy_result = 'DELIVERY_POLICY_PASS'
             AND sent_at LIKE ?""",
        (contact_id, channel, f"{today}%"),
    ).fetchone()
    count = dict_from_row(row)["cnt"] if row else 0
    max_daily = policy["max_per_contact_per_day"]
    if count >= max_daily:
        return {
            "check": "daily_limit",
            "blocked": True,
            "detail": f"Límite diario alcanzado: {count}/{max_daily}",
        }
    return {"check": "daily_limit", "blocked": False, "detail": f"Envíos hoy: {count}/{max_daily}"}


def _check_weekly_limit(conn, contact_id, channel, tenant_id):
    """Verificación 4: Máximo semanal."""
    policy = _get_policy(conn, channel, tenant_id)
    if not policy:
        return {"check": "weekly_limit", "blocked": False, "detail": "Sin política configurada"}

    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    row = conn.execute(
        """SELECT COUNT(*) as cnt FROM marketing_delivery_log
           WHERE contact_id = ? AND channel = ? AND policy_result = 'DELIVERY_POLICY_PASS'
             AND sent_at >= ?""",
        (contact_id, channel, week_ago),
    ).fetchone()
    count = dict_from_row(row)["cnt"] if row else 0
    max_weekly = policy["max_per_contact_per_week"]
    if count >= max_weekly:
        return {
            "check": "weekly_limit",
            "blocked": True,
            "detail": f"Límite semanal alcanzado: {count}/{max_weekly}",
        }
    return {"check": "weekly_limit", "blocked": False, "detail": f"Envíos esta semana: {count}/{max_weekly}"}


def _check_cooldown(conn, contact_id, channel, tenant_id):
    """Verificación 5: Periodo de enfriamiento."""
    policy = _get_policy(conn, channel, tenant_id)
    if not policy:
        return {"check": "cooldown", "blocked": False, "detail": "Sin política configurada"}

    cooldown_hours = policy["cooldown_hours_after_send"]
    cutoff = (datetime.now() - timedelta(hours=cooldown_hours)).strftime("%Y-%m-%dT%H:%M:%S")
    row = conn.execute(
        """SELECT sent_at FROM marketing_delivery_log
           WHERE contact_id = ? AND channel = ? AND policy_result = 'DELIVERY_POLICY_PASS'
             AND sent_at >= ?
           ORDER BY sent_at DESC LIMIT 1""",
        (contact_id, channel, cutoff),
    ).fetchone()
    if row:
        return {
            "check": "cooldown",
            "blocked": True,
            "detail": f"En periodo de enfriamiento ({cooldown_hours}h). Último envío: {dict_from_row(row)['sent_at']}",
        }
    return {"check": "cooldown", "blocked": False, "detail": f"Fuera del periodo de enfriamiento ({cooldown_hours}h)"}


def _check_duplicate_content(conn, contact_id, channel, content_hash, tenant_id):
    """Verificación 6: Contenido duplicado."""
    policy = _get_policy(conn, channel, tenant_id)
    if not policy:
        return {"check": "duplicate_content", "blocked": False, "detail": "Sin política configurada"}

    days = policy["no_duplicate_content_days"]
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")
    row = conn.execute(
        """SELECT id FROM marketing_delivery_log
           WHERE contact_id = ? AND channel = ? AND content_hash = ?
             AND policy_result = 'DELIVERY_POLICY_PASS' AND sent_at >= ?
           LIMIT 1""",
        (contact_id, channel, content_hash, cutoff),
    ).fetchone()
    if row:
        return {
            "check": "duplicate_content",
            "blocked": True,
            "detail": f"Mismo contenido enviado en los últimos {days} días",
        }
    return {"check": "duplicate_content", "blocked": False, "detail": "Contenido no duplicado"}


def _check_blocked_hours(conn, channel, tenant_id):
    """Verificación 7: Horario restringido."""
    policy = _get_policy(conn, channel, tenant_id)
    if not policy:
        return {"check": "blocked_hours", "blocked": False, "detail": "Sin política configurada"}

    start = policy.get("blocked_hours_start")
    end = policy.get("blocked_hours_end")
    if not start or not end:
        return {"check": "blocked_hours", "blocked": False, "detail": "Sin horario restringido configurado"}

    now = datetime.now().strftime("%H:%M")
    # Manejo de rango nocturno (ej: 22:00 a 08:00)
    if start > end:
        # Rango cruza medianoche
        if now >= start or now < end:
            return {
                "check": "blocked_hours",
                "blocked": True,
                "detail": f"Horario restringido: {start}-{end}. Hora actual: {now}",
            }
    else:
        if start <= now < end:
            return {
                "check": "blocked_hours",
                "blocked": True,
                "detail": f"Horario restringido: {start}-{end}. Hora actual: {now}",
            }
    return {"check": "blocked_hours", "blocked": False, "detail": f"Fuera de horario restringido ({start}-{end})"}


def _check_rejected_campaign(conn, contact_id, campaign_id):
    """Verificación 8: Campaña rechazada previamente."""
    row = conn.execute(
        """SELECT id FROM marketing_suppressions
           WHERE contact_id = ? AND scope = 'campaign' AND scope_campaign_id = ?
             AND revoked_at IS NULL
           LIMIT 1""",
        (contact_id, campaign_id),
    ).fetchone()
    if row:
        return {
            "check": "rejected_campaign",
            "blocked": True,
            "detail": "El contacto rechazó esta campaña previamente",
        }
    return {"check": "rejected_campaign", "blocked": False, "detail": "Campaña no rechazada"}


def _check_valid_contact(conn, contact_id, channel):
    """Verificación 9: Datos de contacto válidos."""
    # En el MVP verificamos que exista algún consentimiento con datos
    row = conn.execute(
        """SELECT contact_id FROM marketing_consents
           WHERE contact_id = ? AND channel = ?
           LIMIT 1""",
        (contact_id, channel),
    ).fetchone()
    if row:
        return {"check": "valid_contact", "blocked": False, "detail": "Contacto con datos registrados"}
    return {
        "check": "valid_contact",
        "blocked": True,
        "detail": "Sin datos de contacto válidos registrados para este canal",
    }


def _check_excluded_segment(conn, contact_id, campaign_id):
    """Verificación 10: Segmento excluido (placeholder para futura segmentación)."""
    # En el MVP no hay segmentos excluidos; la verificación siempre pasa
    return {"check": "excluded_segment", "blocked": False, "detail": "Sin segmentos excluidos configurados"}


def _check_no_molestar(conn, contact_id, tenant_id):
    """Verificación 11: Registro No Molestar del SERNAC."""
    row = conn.execute(
        """SELECT id FROM marketing_suppressions
           WHERE contact_id = ? AND reason = 'no_molestar'
             AND revoked_at IS NULL
             AND (expires_at IS NULL OR expires_at > ?)
           LIMIT 1""",
        (contact_id, datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
    ).fetchone()
    if row:
        return {
            "check": "no_molestar",
            "blocked": True,
            "detail": "Contacto registrado en lista No Molestar (Ley 19.496 art. 28 B, SERNAC)",
        }
    return {"check": "no_molestar", "blocked": False, "detail": "No está en lista No Molestar"}


def _get_policy(conn, channel, tenant_id):
    """Obtiene la política de frecuencia activa para un canal."""
    row = conn.execute(
        """SELECT * FROM marketing_delivery_policies
           WHERE channel = ? AND tenant_id = ? AND active = 1
           LIMIT 1""",
        (channel, tenant_id),
    ).fetchone()
    return dict_from_row(row) if row else None

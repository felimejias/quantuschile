"""
Quantus Marketing Center — Rutas Flask (Blueprint).

Todas las rutas del módulo Marketing Center, protegidas por require_master_login.
Referencia: implementation_plan.md v2, §6, §9.

Protocolo de Despliegue: Este módulo se desarrolla y prueba en Staging.
Sin publicación real automática en la Fase 1.
"""

import hashlib
import json
import uuid
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session

from marketing.db import get_db_conn, ensure_marketing_db, dict_from_row, dicts_from_rows
from marketing.state_machine import (
    can_transition, validate_transition,
    DRAFT, GENERATED, COMPLIANCE_REVIEW, HUMAN_REVIEW,
    APPROVED, SCHEDULED, CANCELLED, ARCHIVED,
    COMPLIANCE_BLOCKED, CHANGES_REQUESTED,
)
from marketing.rbac import (
    get_role_for_session, check_permission,
    can_approve_own_content, can_lift_compliance_block,
    MARKETING_ADMIN,
)
from marketing.claims_matrix import check_text_compliance
from marketing.utm_builder import build_utm_url
from marketing.agents.compliance import run_compliance_check


marketing_bp = Blueprint(
    "marketing",
    __name__,
    template_folder="../templates/marketing",
    url_prefix="/marketing",
)


def _require_master():
    """Reutiliza la autenticación del maestro existente en app.py."""
    if not session.get("quantus_master_authenticated"):
        return redirect(url_for("maestro_login", next=request.path))
    return None


def _get_role():
    """Obtiene el rol RBAC del usuario actual."""
    return get_role_for_session(session)


def _audit(conn, flow_type, actor, role, action, entity_type, entity_id,
           old_value=None, new_value=None, reason=None):
    """Registra una acción en la tabla de auditoría correspondiente."""
    table = "marketing_organic_audit" if flow_type == "ORGANIC" else "marketing_direct_audit"
    conn.execute(
        f"""INSERT INTO {table}
            (id, tenant_id, actor, actor_role, action, entity_type, entity_id,
             old_value, new_value, reason, ip_address, user_agent)
            VALUES (?, 'quantus', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            str(uuid.uuid4()),
            actor,
            role,
            action,
            entity_type,
            entity_id,
            json.dumps(old_value) if old_value else None,
            json.dumps(new_value) if new_value else None,
            reason,
            request.remote_addr if request else None,
            request.user_agent.string if request else None,
        ),
    )


# ============================================================================
# Inicialización (asegurar tablas al importar)
# ============================================================================
@marketing_bp.before_app_request
def _init_marketing_db():
    """Crea las tablas de marketing en el primer request (idempotente)."""
    if not getattr(marketing_bp, "_db_initialized", False):
        try:
            ensure_marketing_db()
            marketing_bp._db_initialized = True
        except Exception as e:
            import logging
            logging.getLogger("QuantusPortal").error(f"Error inicializando marketing DB: {e}")


# ============================================================================
# DASHBOARD
# ============================================================================
@marketing_bp.route("/")
def dashboard():
    guard = _require_master()
    if guard:
        return guard
    role = _get_role()

    conn = get_db_conn()
    try:
        # Estadísticas
        campaigns = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM marketing_campaigns GROUP BY status"
        ).fetchall()
        contents = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM marketing_contents GROUP BY status"
        ).fetchall()
        leads = conn.execute(
            "SELECT lead_status, COUNT(*) as cnt FROM marketing_leads GROUP BY lead_status"
        ).fetchall()

        # Últimas campañas
        recent = conn.execute(
            """SELECT * FROM marketing_campaigns
               ORDER BY created_at DESC LIMIT 10"""
        ).fetchall()

        return render_template(
            "dashboard.html",
            campaign_stats=dicts_from_rows(campaigns),
            content_stats=dicts_from_rows(contents),
            lead_stats=dicts_from_rows(leads),
            recent_campaigns=dicts_from_rows(recent),
            role=role,
        )
    finally:
        conn.close()


# ============================================================================
# CAMPAÑAS
# ============================================================================
@marketing_bp.route("/campaigns/")
def campaigns_list():
    guard = _require_master()
    if guard:
        return guard
    role = _get_role()

    conn = get_db_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM marketing_campaigns ORDER BY created_at DESC"
        ).fetchall()
        return render_template(
            "campaigns.html",
            campaigns=dicts_from_rows(rows),
            role=role,
        )
    finally:
        conn.close()


@marketing_bp.route("/campaigns/new", methods=["GET", "POST"])
def campaign_new():
    guard = _require_master()
    if guard:
        return guard
    role = _get_role()
    try:
        check_permission(role, "create")
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    if request.method == "POST":
        data = request.form
        campaign_id = str(uuid.uuid4())
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        conn = get_db_conn()
        try:
            conn.execute(
                """INSERT INTO marketing_campaigns
                   (id, tenant_id, name, service_category, target_audience,
                    flow_type, status, created_by, created_at, updated_at)
                   VALUES (?, 'quantus', ?, ?, ?, ?, 'DRAFT', ?, ?, ?)""",
                (
                    campaign_id,
                    data.get("name", "").strip(),
                    data.get("service_category", ""),
                    data.get("target_audience", ""),
                    data.get("flow_type", "ORGANIC"),
                    session.get("quantus_master_user", "admin"),
                    now,
                    now,
                ),
            )
            conn.commit()

            _audit(
                conn, data.get("flow_type", "ORGANIC"),
                session.get("quantus_master_user", "admin"), role,
                "CREATE", "campaign", campaign_id,
                new_value={"name": data.get("name"), "service_category": data.get("service_category")},
            )
            conn.commit()

            return redirect(url_for("marketing.campaign_detail", campaign_id=campaign_id))
        finally:
            conn.close()

    return render_template("campaign_new.html", role=role)


@marketing_bp.route("/campaigns/<campaign_id>")
def campaign_detail(campaign_id):
    guard = _require_master()
    if guard:
        return guard
    role = _get_role()

    conn = get_db_conn()
    try:
        campaign = dict_from_row(
            conn.execute("SELECT * FROM marketing_campaigns WHERE id = ?", (campaign_id,)).fetchone()
        )
        if not campaign:
            return "Campaña no encontrada", 404

        contents = dicts_from_rows(
            conn.execute(
                "SELECT * FROM marketing_contents WHERE campaign_id = ? ORDER BY channel",
                (campaign_id,),
            ).fetchall()
        )

        approvals = {}
        for c in contents:
            appr = conn.execute(
                "SELECT * FROM marketing_approvals WHERE content_id = ? ORDER BY created_at DESC LIMIT 1",
                (c["id"],),
            ).fetchone()
            if appr:
                approvals[c["id"]] = dict_from_row(appr)

        schedules = dicts_from_rows(
            conn.execute(
                "SELECT * FROM marketing_schedules WHERE content_id IN (SELECT id FROM marketing_contents WHERE campaign_id = ?)",
                (campaign_id,),
            ).fetchall()
        )

        return render_template(
            "campaign_detail.html",
            campaign=campaign,
            contents=contents,
            approvals=approvals,
            schedules=schedules,
            role=role,
        )
    finally:
        conn.close()


# ============================================================================
# CALENDARIO
# ============================================================================
@marketing_bp.route("/calendar")
def calendar_view():
    guard = _require_master()
    if guard:
        return guard
    role = _get_role()

    conn = get_db_conn()
    try:
        schedules = dicts_from_rows(conn.execute(
            """SELECT s.*, c.title, c.channel, c.body, camp.name as campaign_name,
                      camp.service_category
               FROM marketing_schedules s
               JOIN marketing_contents c ON s.content_id = c.id
               JOIN marketing_campaigns camp ON c.campaign_id = camp.id
               ORDER BY s.scheduled_at"""
        ).fetchall())

        return render_template("calendar.html", schedules=schedules, role=role)
    finally:
        conn.close()


# ============================================================================
# PROSPECTOS (LEADS)
# ============================================================================
@marketing_bp.route("/leads")
def leads_list():
    guard = _require_master()
    if guard:
        return guard
    role = _get_role()

    conn = get_db_conn()
    try:
        leads = dicts_from_rows(conn.execute(
            "SELECT * FROM marketing_leads ORDER BY created_at DESC"
        ).fetchall())
        return render_template("leads.html", leads=leads, role=role)
    finally:
        conn.close()


# ============================================================================
# LISTA DE SUPRESIÓN
# ============================================================================
@marketing_bp.route("/suppressions")
def suppressions_list():
    guard = _require_master()
    if guard:
        return guard
    role = _get_role()

    conn = get_db_conn()
    try:
        suppressions = dicts_from_rows(conn.execute(
            "SELECT * FROM marketing_suppressions WHERE revoked_at IS NULL ORDER BY created_at DESC"
        ).fetchall())
        return render_template("suppressions.html", suppressions=suppressions, role=role)
    finally:
        conn.close()


# ============================================================================
# APIs
# ============================================================================
@marketing_bp.route("/api/generate", methods=["POST"])
def api_generate_content():
    """Genera contenido multicanal para una campaña (MVP: simulado)."""
    guard = _require_master()
    if guard:
        return jsonify({"error": "No autenticado"}), 401
    role = _get_role()
    try:
        check_permission(role, "create")
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    data = request.get_json()
    campaign_id = data.get("campaign_id")
    if not campaign_id:
        return jsonify({"error": "campaign_id requerido"}), 400

    conn = get_db_conn()
    try:
        campaign = dict_from_row(
            conn.execute("SELECT * FROM marketing_campaigns WHERE id = ?", (campaign_id,)).fetchone()
        )
        if not campaign:
            return jsonify({"error": "Campaña no encontrada"}), 404

        service = campaign["service_category"]
        channels = _channels_for_flow(campaign["flow_type"])
        created_contents = []

        for channel_info in channels:
            channel = channel_info["channel"]
            flow = channel_info["flow_type"]
            content_type = channel_info["content_type"]

            # Generar texto por canal (MVP: plantilla básica)
            body = _generate_mvp_text(service, channel, campaign["name"])
            destination_url = build_utm_url(service, channel, campaign["name"])

            content_hash = hashlib.sha256(
                f"{body}{channel}{campaign_id}".encode()
            ).hexdigest()

            content_id = str(uuid.uuid4())
            now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

            conn.execute(
                """INSERT INTO marketing_contents
                   (id, campaign_id, channel, flow_type, content_type, title,
                    body, hashtags, destination_url, content_hash,
                    ai_model_used, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'GENERATED', ?, ?)""",
                (
                    content_id, campaign_id, channel, flow, content_type,
                    f"{campaign['name']} — {channel}",
                    body,
                    _generate_hashtags(service),
                    destination_url,
                    content_hash,
                    "mvp_template_v1",
                    now, now,
                ),
            )
            created_contents.append({
                "id": content_id,
                "channel": channel,
                "flow_type": flow,
            })

        # Actualizar estado de la campaña
        conn.execute(
            "UPDATE marketing_campaigns SET status = 'ACTIVE', updated_at = ? WHERE id = ?",
            (datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), campaign_id),
        )
        conn.commit()

        _audit(
            conn, campaign["flow_type"],
            session.get("quantus_master_user", "admin"), role,
            "CREATE", "content", campaign_id,
            new_value={"contents_generated": len(created_contents)},
        )
        conn.commit()

        return jsonify({
            "status": "ok",
            "campaign_id": campaign_id,
            "contents_created": created_contents,
        })
    finally:
        conn.close()


@marketing_bp.route("/api/compliance-check", methods=["POST"])
def api_compliance_check():
    """Ejecuta verificación de cumplimiento en un contenido."""
    guard = _require_master()
    if guard:
        return jsonify({"error": "No autenticado"}), 401

    data = request.get_json()
    content_id = data.get("content_id")
    if not content_id:
        return jsonify({"error": "content_id requerido"}), 400

    conn = get_db_conn()
    try:
        content = dict_from_row(
            conn.execute("SELECT * FROM marketing_contents WHERE id = ?", (content_id,)).fetchone()
        )
        if not content:
            return jsonify({"error": "Contenido no encontrado"}), 404

        campaign = dict_from_row(
            conn.execute("SELECT * FROM marketing_campaigns WHERE id = ?", (content["campaign_id"],)).fetchone()
        )

        # Ejecutar compliance check
        result = run_compliance_check(content, campaign["service_category"])

        # Guardar resultado
        approval_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO marketing_approvals
               (id, content_id, compliance_status, compliance_checks,
                claims_validated, claims_blocked)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                approval_id,
                content_id,
                result["overall_status"],
                json.dumps(result["checks"]),
                json.dumps(result["claims_validated"]),
                json.dumps(result["claims_blocked"]),
            ),
        )

        # Actualizar estado del contenido
        if result["overall_status"] == "BLOCKED":
            new_status = COMPLIANCE_BLOCKED
        else:
            new_status = HUMAN_REVIEW

        try:
            validate_transition(content["status"], new_status)
            conn.execute(
                "UPDATE marketing_contents SET status = ?, updated_at = ? WHERE id = ?",
                (new_status, datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), content_id),
            )
        except ValueError:
            # Si la transición no es válida desde el estado actual,
            # primero intentar COMPLIANCE_REVIEW
            try:
                validate_transition(content["status"], COMPLIANCE_REVIEW)
                conn.execute(
                    "UPDATE marketing_contents SET status = ?, updated_at = ? WHERE id = ?",
                    (COMPLIANCE_REVIEW, datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), content_id),
                )
            except ValueError:
                pass

        conn.commit()

        return jsonify({
            "status": "ok",
            "compliance_result": result,
            "content_status": new_status,
        })
    finally:
        conn.close()


@marketing_bp.route("/api/approve", methods=["POST"])
def api_approve():
    """Aprueba o rechaza un contenido."""
    guard = _require_master()
    if guard:
        return jsonify({"error": "No autenticado"}), 401
    role = _get_role()
    try:
        check_permission(role, "approve")
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    data = request.get_json()
    content_id = data.get("content_id")
    action = data.get("action")  # 'approve' o 'request_changes'
    reason = data.get("reason", "")

    if not content_id or action not in ("approve", "request_changes"):
        return jsonify({"error": "content_id y action ('approve'/'request_changes') requeridos"}), 400

    conn = get_db_conn()
    try:
        content = dict_from_row(
            conn.execute("SELECT * FROM marketing_contents WHERE id = ?", (content_id,)).fetchone()
        )
        if not content:
            return jsonify({"error": "Contenido no encontrado"}), 404

        actor = session.get("quantus_master_user", "admin")

        # Separación de funciones: no aprobar propio contenido
        campaign = dict_from_row(
            conn.execute("SELECT * FROM marketing_campaigns WHERE id = ?", (content["campaign_id"],)).fetchone()
        )
        if action == "approve":
            allowed, msg = can_approve_own_content(actor, campaign.get("created_by", ""), role)
            if not allowed:
                return jsonify({"error": msg}), 403

        if action == "approve":
            new_status = APPROVED
        else:
            new_status = CHANGES_REQUESTED

        try:
            validate_transition(content["status"], new_status)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        conn.execute(
            "UPDATE marketing_contents SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, now, content_id),
        )

        # Actualizar aprobación
        conn.execute(
            """UPDATE marketing_approvals SET approved_by = ?, approved_at = ?,
               approval_role = ?, rejection_reason = ?, changes_requested_log = ?
               WHERE content_id = ? AND id = (
                   SELECT id FROM marketing_approvals WHERE content_id = ?
                   ORDER BY created_at DESC LIMIT 1
               )""",
            (
                actor if action == "approve" else None,
                now if action == "approve" else None,
                role,
                reason if action == "request_changes" else None,
                json.dumps({"reason": reason, "requested_by": actor, "at": now}) if action == "request_changes" else None,
                content_id, content_id,
            ),
        )
        conn.commit()

        _audit(
            conn, content["flow_type"],
            actor, role,
            "APPROVE" if action == "approve" else "REJECT",
            "content", content_id,
            old_value={"status": content["status"]},
            new_value={"status": new_status},
            reason=reason,
        )
        conn.commit()

        return jsonify({"status": "ok", "content_status": new_status})
    finally:
        conn.close()


@marketing_bp.route("/api/schedule", methods=["POST"])
def api_schedule():
    """Simula programación de un contenido aprobado."""
    guard = _require_master()
    if guard:
        return jsonify({"error": "No autenticado"}), 401
    role = _get_role()
    try:
        check_permission(role, "schedule")
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    data = request.get_json()
    content_id = data.get("content_id")
    scheduled_at = data.get("scheduled_at")

    if not content_id or not scheduled_at:
        return jsonify({"error": "content_id y scheduled_at requeridos"}), 400

    conn = get_db_conn()
    try:
        content = dict_from_row(
            conn.execute("SELECT * FROM marketing_contents WHERE id = ?", (content_id,)).fetchone()
        )
        if not content:
            return jsonify({"error": "Contenido no encontrado"}), 404

        try:
            validate_transition(content["status"], SCHEDULED)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        # Generar idempotency_key
        idempotency_key = hashlib.sha256(
            f"{content['campaign_id']}{content_id}{content['channel']}quantus{scheduled_at}".encode()
        ).hexdigest()

        # Verificar duplicado
        existing = conn.execute(
            "SELECT id FROM marketing_schedules WHERE idempotency_key = ?", (idempotency_key,)
        ).fetchone()
        if existing:
            return jsonify({"error": "Esta programación ya existe (idempotencia)"}), 409

        schedule_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO marketing_schedules
               (id, content_id, flow_type, channel, scheduled_at,
                idempotency_key, content_hash, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'SCHEDULED')""",
            (
                schedule_id,
                content_id,
                content["flow_type"],
                content["channel"],
                scheduled_at,
                idempotency_key,
                content["content_hash"],
            ),
        )

        conn.execute(
            "UPDATE marketing_contents SET status = 'SCHEDULED', updated_at = ? WHERE id = ?",
            (datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), content_id),
        )
        conn.commit()

        _audit(
            conn, content["flow_type"],
            session.get("quantus_master_user", "admin"), role,
            "SCHEDULE", "schedule", schedule_id,
            new_value={"content_id": content_id, "scheduled_at": scheduled_at},
        )
        conn.commit()

        return jsonify({
            "status": "ok",
            "schedule_id": schedule_id,
            "note": "Simulación de programación (MVP — sin publicación real)",
        })
    finally:
        conn.close()


@marketing_bp.route("/api/cancel", methods=["POST"])
def api_cancel():
    """Cancela un contenido o una campaña completa."""
    guard = _require_master()
    if guard:
        return jsonify({"error": "No autenticado"}), 401
    role = _get_role()
    try:
        check_permission(role, "cancel")
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    data = request.get_json()
    campaign_id = data.get("campaign_id")
    content_id = data.get("content_id")
    reason = data.get("reason", "Cancelación manual")

    conn = get_db_conn()
    try:
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        if campaign_id:
            # Cancelar toda la campaña
            contents = dicts_from_rows(conn.execute(
                "SELECT id, status, flow_type FROM marketing_contents WHERE campaign_id = ?",
                (campaign_id,),
            ).fetchall())

            cancelled_count = 0
            for c in contents:
                allowed, _ = can_transition(c["status"], CANCELLED)
                if allowed:
                    conn.execute(
                        "UPDATE marketing_contents SET status = 'CANCELLED', updated_at = ? WHERE id = ?",
                        (now, c["id"]),
                    )
                    cancelled_count += 1

            conn.execute(
                "UPDATE marketing_campaigns SET status = 'CANCELLED', updated_at = ? WHERE id = ?",
                (now, campaign_id),
            )
            conn.commit()

            _audit(
                conn, "ORGANIC",
                session.get("quantus_master_user", "admin"), role,
                "CANCEL", "campaign", campaign_id,
                new_value={"cancelled_contents": cancelled_count},
                reason=reason,
            )
            conn.commit()

            return jsonify({"status": "ok", "cancelled_contents": cancelled_count})

        elif content_id:
            content = dict_from_row(
                conn.execute("SELECT * FROM marketing_contents WHERE id = ?", (content_id,)).fetchone()
            )
            if not content:
                return jsonify({"error": "Contenido no encontrado"}), 404

            try:
                validate_transition(content["status"], CANCELLED)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

            conn.execute(
                "UPDATE marketing_contents SET status = 'CANCELLED', updated_at = ? WHERE id = ?",
                (now, content_id),
            )
            conn.commit()

            return jsonify({"status": "ok"})

        return jsonify({"error": "campaign_id o content_id requerido"}), 400
    finally:
        conn.close()


# ============================================================================
# Helpers de generación MVP
# ============================================================================
def _channels_for_flow(flow_type):
    """Retorna los canales según el tipo de flujo."""
    organic = [
        {"channel": "instagram", "flow_type": "ORGANIC", "content_type": "post"},
        {"channel": "facebook", "flow_type": "ORGANIC", "content_type": "post"},
        {"channel": "linkedin", "flow_type": "ORGANIC", "content_type": "article"},
    ]
    direct = [
        {"channel": "whatsapp_template", "flow_type": "DIRECT", "content_type": "template"},
    ]
    if flow_type == "ORGANIC":
        return organic
    elif flow_type == "DIRECT":
        return direct
    else:  # BOTH
        return organic + direct


def _generate_mvp_text(service, channel, campaign_name):
    """Genera texto básico de ejemplo por canal (MVP placeholder)."""
    service_names = {
        "diario_oficial": "Radar Diario Oficial",
        "licitaciones": "Radar Licitaciones 24/7",
        "inapi": "Registro y Vigilancia de Marcas",
        "remates": "Radar de Remates",
        "ley_21719": "Preparación Ley 21.719",
        "erp": "Quantus ERP",
        "agentes_ia": "Agentes de IA Empresariales",
    }
    service_name = service_names.get(service, service)

    templates = {
        "instagram": (
            f"🔍 {service_name}\n\n"
            f"¿Sabías que puedes automatizar el monitoreo de información crítica para tu empresa?\n\n"
            f"Quantus Chile te ayuda con herramientas de IA diseñadas para pymes y empresas.\n\n"
            f"Conoce más en el enlace de nuestro perfil.\n\n"
            f"Quantus Chile SpA — Plataforma privada de servicios empresariales."
        ),
        "facebook": (
            f"📋 {service_name}\n\n"
            f"En Quantus Chile trabajamos con agentes de inteligencia artificial para "
            f"ayudar a empresas y emprendedores a monitorear información relevante de "
            f"manera eficiente.\n\n"
            f"Nuestro servicio de {service_name} está diseñado para simplificar procesos "
            f"que normalmente requieren revisión manual constante.\n\n"
            f"¿Quieres saber cómo funciona? Visita nuestro sitio.\n\n"
            f"Quantus Chile SpA — Plataforma privada de servicios empresariales.\n"
            f"Quantus Chile SpA es una plataforma privada y no representa ni mantiene "
            f"afiliación oficial con los organismos mencionados."
        ),
        "linkedin": (
            f"🏢 {service_name} — Automatización para empresas\n\n"
            f"Las empresas que procesan información de fuentes públicas enfrentan un "
            f"desafío constante: la revisión manual consume tiempo y recursos.\n\n"
            f"En Quantus Chile SpA desarrollamos herramientas basadas en inteligencia "
            f"artificial que asisten en el monitoreo y análisis de información empresarial "
            f"relevante.\n\n"
            f"Nuestro servicio de {service_name} ayuda a identificar coincidencias y "
            f"oportunidades compatibles con los criterios configurados por cada empresa.\n\n"
            f"Quantus Chile SpA — Plataforma privada de servicios empresariales.\n"
            f"Quantus Chile SpA es una plataforma privada y no representa ni mantiene "
            f"afiliación oficial con los organismos mencionados."
        ),
        "whatsapp_template": (
            f"Hola {{{{1}}}} 👋\n\n"
            f"Quantus Chile tiene una herramienta de {service_name} que podría interesarte.\n\n"
            f"Conoce el servicio: {{{{2}}}}\n\n"
            f"Quantus Chile SpA\n"
            f"Si no deseas recibir más mensajes, responde CANCELAR."
        ),
    }
    return templates.get(channel, templates["instagram"])


def _generate_hashtags(service):
    """Genera hashtags relevantes por servicio (máximo 5)."""
    base = "#QuantusChile #IA #Automatización"
    service_tags = {
        "diario_oficial": "#DiarioOficial #MonitoreoEmpresarial",
        "licitaciones": "#Licitaciones #MercadoPublico",
        "inapi": "#Marcas #PropiedadIndustrial",
        "remates": "#Remates #Inversiones",
        "ley_21719": "#ProtecciónDeDatos #Ley21719",
        "erp": "#ERP #GestiónEmpresarial",
        "agentes_ia": "#InteligenciaArtificial #Pymes",
    }
    return f"{base} {service_tags.get(service, '')}"

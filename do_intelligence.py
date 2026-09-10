import hashlib
import html
import json
import os
import sqlite3
import textwrap
import uuid
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = DATA_DIR / "do_reports"
DB_PATH = DATA_DIR / "do_intelligence.sqlite3"
LOGO_PATH = BASE_DIR / "static" / "quantus-logo-clean.png"
DIARIO_OFICIAL_FUENTE = "https://www.diariooficial.interior.gob.cl"
MATCH_TYPE_LABELS = {
    "exacta_rut": "Coincidencia exacta por RUT",
    "exacta_nombre": "Coincidencia exacta por nombre",
    "posible": "Posible coincidencia (verificar en fuente oficial)",
    "parcial": "Coincidencia parcial (posible errata en la fuente)",
    "alias": "Alias / empresa asociada",
}
DEFAULT_LAWYER_URL = (
    "mailto:contacto@quantuschile.cl"
    "?subject=Derivacion%20abogado%20recomendado%20Radar%20Diario%20Oficial"
)


def get_db_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn

def ensure_storage():
    DATA_DIR.mkdir(exist_ok=True)
    REPORT_DIR.mkdir(exist_ok=True)
    with get_db_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS do_ai_reports (
                id TEXT PRIMARY KEY,
                module TEXT NOT NULL DEFAULT 'diario_oficial',
                created_at TEXT NOT NULL,
                client_name TEXT,
                client_rut TEXT,
                client_email TEXT,
                source_hash TEXT NOT NULL,
                source_excerpt TEXT NOT NULL,
                ai_json TEXT NOT NULL,
                urgency TEXT,
                publication_type TEXT,
                provider TEXT,
                mode TEXT,
                pdf_path TEXT
            )
            """
        )
        try:
            conn.execute("ALTER TABLE do_ai_reports ADD COLUMN module TEXT NOT NULL DEFAULT 'diario_oficial'")
        except sqlite3.OperationalError:
            pass
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS do_client_memory (
                client_key TEXT PRIMARY KEY,
                display_name TEXT,
                rut TEXT,
                email TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                total_alerts INTEGER NOT NULL DEFAULT 0,
                high_risk_alerts INTEGER NOT NULL DEFAULT 0,
                last_summary TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS master_client_registry (
                registry_key TEXT PRIMARY KEY,
                rut TEXT,
                clean_rut TEXT,
                display_name TEXT,
                email TEXT,
                phone TEXT,
                source_module TEXT NOT NULL,
                source_ref TEXT,
                status TEXT NOT NULL DEFAULT 'activo',
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                alert_count INTEGER NOT NULL DEFAULT 0,
                last_alert_at TEXT,
                last_alert_summary TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_master_client_registry_clean_rut ON master_client_registry(clean_rut)"
        )


def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def compact_key(*values):
    raw = "|".join((value or "").strip().lower() for value in values)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def source_digest(source_text):
    return hashlib.sha256((source_text or "").encode("utf-8")).hexdigest()


def clean_registry_rut(rut):
    return (rut or "").replace(".", "").replace("-", "").strip().upper()


def listify(value):
    if isinstance(value, list):
        return [str(item) for item in value]
    if not value:
        return []
    return [str(value)]


def module_title(module):
    titles = {
        "diario_oficial": "Informe Quantus Diario Oficial",
        "inapi": "Informe Quantus Viabilidad de Marca",
        "licitaciones": "Informe Quantus Licitaciones",
        "erp": "Informe Quantus ERP",
    }
    return titles.get(module, "Informe Quantus")


def recommended_lawyer():
    return {
        "name": os.getenv("DO_RECOMMENDED_LAWYER_NAME", "Abogado recomendado por Quantus"),
        "url": os.getenv("DO_RECOMMENDED_LAWYER_URL", DEFAULT_LAWYER_URL),
        "note": os.getenv(
            "DO_RECOMMENDED_LAWYER_NOTE",
            "El contacto se entrega como recomendacion para revisar la fuente oficial y decidir acciones; Quantus no reemplaza la asesoria juridica humana."
        ),
    }


def render_pdf(report_id, ai_data, source_text, client=None, module="diario_oficial", match_info=None):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except Exception as exc:
        raise RuntimeError("reportlab no esta instalado en el servidor") from exc

    pdf_path = REPORT_DIR / f"{report_id}.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=0.62 * inch,
        leftMargin=0.62 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title=module_title(module),
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "QuantusTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#06101f"),
        spaceAfter=8,
    )
    h2 = ParagraphStyle(
        "QuantusH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "QuantusBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.2,
        leading=13,
        textColor=colors.HexColor("#1f2937"),
    )
    small = ParagraphStyle(
        "QuantusSmall",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b"),
    )
    callout = ParagraphStyle(
        "QuantusCallout",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=9.3,
        leading=13,
        textColor=colors.HexColor("#075985"),
    )

    story = []
    if LOGO_PATH.exists():
        story.append(Image(str(LOGO_PATH), width=0.72 * inch, height=0.72 * inch))
        story.append(Spacer(1, 8))
    story.append(Paragraph(module_title(module), title))
    story.append(Paragraph(f"Generado: {now_iso()} | ID: {report_id}", small))
    story.append(Spacer(1, 12))

    urgency = str(ai_data.get("nivel_urgencia") or "medio").upper()
    publication_type = str(ai_data.get("tipo_publicacion") or "Publicacion oficial")
    provider = str(ai_data.get("proveedor_ia") or "Gemini")
    client = client or {}
    metadata = [
        ["Urgencia", urgency],
        ["Tipo", publication_type],
        ["Proveedor IA", provider],
        ["Cliente", client.get("nombre") or "No informado"],
        ["RUT", client.get("rut") or "No informado"],
    ]
    match_info = match_info or {}
    match_label = MATCH_TYPE_LABELS.get(match_info.get("match_type")) or match_info.get("match_label")
    if match_label:
        metadata.insert(1, ["Coincidencia", match_label])
    table = Table(metadata, colWidths=[1.45 * inch, 4.85 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e0f2fe")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.4),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)

    story.append(Paragraph("Resumen ejecutivo", h2))
    story.append(Paragraph(str(ai_data.get("resumen_ejecutivo") or "No informado."), body))

    for heading, key in [
        ("Por que importa", "por_que_importa"),
        ("Acciones recomendadas", "acciones_recomendadas"),
        ("Datos a verificar", "datos_a_verificar"),
    ]:
        story.append(Paragraph(heading, h2))
        items = listify(ai_data.get(key))
        for item in items or ["No informado."]:
            story.append(Paragraph(f"- {item}", body))

    story.append(Paragraph("Plazos posibles", h2))
    story.append(Paragraph(str(ai_data.get("plazos_posibles") or "No informado."), body))

    story.append(Paragraph("Fuente oficial", h2))
    fuente_url = html.escape(str(match_info.get("source_url") or DIARIO_OFICIAL_FUENTE), quote=True)
    story.append(Paragraph(
        f'Revisa la publicacion en la fuente oficial: <a href="{fuente_url}" color="#0284c7">{fuente_url}</a>. '
        "La fuente oficial u organismos publicadores pueden presentar errores, omisiones, abreviaciones, "
        "tildes distintas, nombres incompletos, RUT mal digitado u omitido, razon social parcial o referencias "
        "a representantes legales. Confirma datos y plazos directamente en la publicacion oficial o con asesoria legal.",
        body,
    ))

    story.append(Paragraph("Mensaje sugerido para cliente", h2))
    story.append(Paragraph(str(ai_data.get("mensaje_cliente") or "No informado."), body))

    if module == "diario_oficial":
        lawyer = recommended_lawyer()
        lawyer_name = html.escape(lawyer["name"])
        lawyer_url = html.escape(lawyer["url"], quote=True)
        lawyer_note = html.escape(lawyer["note"])
        advisory_text = (
            "Quantus ya reviso el PDF o texto oficial, lo explico en simple y ordeno "
            "los pasos iniciales. Si esta alerta contiene un plazo, citacion, oposicion, "
            "remate, demanda, afectacion patrimonial o dato que deba ser contestado, "
            "revisa la fuente oficial y consulta asesoria juridica cuanto antes. "
            f'<a href="{lawyer_url}" color="#0284c7">{lawyer_name}</a>. '
            f"{lawyer_note}"
        )
        advisory = Table(
            [[Paragraph(advisory_text, callout)]],
            colWidths=[6.3 * inch],
        )
        advisory.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#e0f2fe")),
            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#38bdf8")),
            ("PADDING", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(KeepTogether([
            Paragraph("Siguiente accion recomendada", h2),
            advisory,
        ]))

    story.append(Paragraph("Extracto analizado", h2))
    excerpt = (source_text or "")[:1800]
    story.append(Paragraph("<br/>".join(textwrap.wrap(excerpt, width=96)) or "No informado.", small))

    story.append(Paragraph("Advertencia", h2))
    story.append(Paragraph(str(ai_data.get("advertencia") or "Este analisis no reemplaza revision legal humana."), small))
    doc.build(story)
    return str(pdf_path)


def save_report(ai_data, source_text, client=None, mode="free", module="diario_oficial", match_info=None):
    ensure_storage()
    report_id = uuid.uuid4().hex[:16]
    client = client or {}
    pdf_path = render_pdf(report_id, ai_data, source_text, client=client, module=module, match_info=match_info)
    created_at = now_iso()
    urgency = str(ai_data.get("nivel_urgencia") or "medio").lower()
    publication_type = str(ai_data.get("tipo_publicacion") or "")
    provider = str(ai_data.get("proveedor_ia") or "")
    source_excerpt = (source_text or "")[:4000]

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO do_ai_reports (
                id, module, created_at, client_name, client_rut, client_email, source_hash,
                source_excerpt, ai_json, urgency, publication_type, provider, mode, pdf_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                module,
                created_at,
                client.get("nombre"),
                client.get("rut"),
                client.get("email"),
                source_digest(source_text),
                source_excerpt,
                json.dumps(ai_data, ensure_ascii=False),
                urgency,
                publication_type,
                provider,
                mode,
                pdf_path,
            ),
        )
        update_memory(conn, client, ai_data, created_at)

    _audit_report_ready(report_id, client, module, urgency, match_info)

    return {
        "report_id": report_id,
        "pdf_path": pdf_path,
        "report_url": f"/informes/{report_id}.pdf",
    }


def _audit_report_ready(report_id, client, module, urgency, match_info=None):
    """Registra la generacion del PDF en el historial auditable de comunicaciones."""
    try:
        from communications.audit_log import record_communication
        match_info = match_info or {}
        record_communication(
            module=module or "diario_oficial",
            client_key=(client or {}).get("key") or "",
            client_name=(client or {}).get("nombre") or "",
            client_rut=(client or {}).get("rut") or "",
            channel="pdf",
            event_type="report_ready",
            subject=f"Informe {report_id} listo",
            message="Informe ejecutivo PDF generado y disponible.",
            report_url=f"/informes/{report_id}.pdf",
            status="sent",
            provider_response=f"report_id={report_id}",
            source_hash=report_id,
            urgency=urgency,
            client=client,
            payload={"informe_id": report_id, "match_type": (match_info or {}).get("match_type") or ""},
        )
    except Exception as exc:
        print(f"[DO Intelligence] No se pudo auditar report_ready {report_id}: {exc}")


def update_memory(conn, client, ai_data, created_at):
    nombre = (client.get("nombre") or "").strip()
    rut = (client.get("rut") or "").strip()
    email = (client.get("email") or "").strip()
    if not (nombre or rut or email):
        return
    client_key = compact_key(nombre, rut, email)
    urgency = str(ai_data.get("nivel_urgencia") or "").lower()
    high_risk = 1 if urgency in {"alto", "critico"} else 0
    summary = str(ai_data.get("resumen_ejecutivo") or "")[:800]
    existing = conn.execute(
        "SELECT total_alerts, high_risk_alerts FROM do_client_memory WHERE client_key = ?",
        (client_key,),
    ).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE do_client_memory
            SET display_name = ?, rut = ?, email = ?, last_seen = ?,
                total_alerts = ?, high_risk_alerts = ?, last_summary = ?
            WHERE client_key = ?
            """,
            (
                nombre,
                rut,
                email,
                created_at,
                int(existing[0]) + 1,
                int(existing[1]) + high_risk,
                summary,
                client_key,
            ),
        )
    else:
        conn.execute(
            """
            INSERT INTO do_client_memory (
                client_key, display_name, rut, email, first_seen, last_seen,
                total_alerts, high_risk_alerts, last_summary
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (client_key, nombre, rut, email, created_at, created_at, 1, high_risk, summary),
        )


def registry_key_for(source_module, rut=None, display_name=None, email=None, source_ref=None):
    return compact_key(source_module or "", clean_registry_rut(rut), display_name or "", email or "", source_ref or "")


def upsert_registry_client(source_module, display_name=None, rut=None, email=None, phone=None, source_ref=None, status="activo"):
    ensure_storage()
    display_name = (display_name or "").strip()
    rut = (rut or "").strip()
    email = (email or "").strip()
    phone = (phone or "").strip()
    clean_rut = clean_registry_rut(rut)
    if not (clean_rut or display_name or email):
        return None
    key = registry_key_for(source_module, rut, display_name, email, source_ref)
    now = now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        existing = conn.execute(
            "SELECT registry_key FROM master_client_registry WHERE registry_key = ?",
            (key,),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE master_client_registry
                SET rut = ?, clean_rut = ?, display_name = ?, email = ?, phone = ?,
                    source_module = ?, source_ref = ?, status = ?, last_seen = ?
                WHERE registry_key = ?
                """,
                (rut, clean_rut, display_name, email, phone, source_module, source_ref, status, now, key),
            )
        else:
            conn.execute(
                """
                INSERT INTO master_client_registry (
                    registry_key, rut, clean_rut, display_name, email, phone, source_module,
                    source_ref, status, first_seen, last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (key, rut, clean_rut, display_name, email, phone, source_module, source_ref, status, now, now),
            )
    return key


def registry_matches_for_rut(rut):
    ensure_storage()
    clean_rut = clean_registry_rut(rut)
    if not clean_rut:
        return []
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(
            """
            SELECT * FROM master_client_registry
            WHERE clean_rut = ?
            ORDER BY last_seen DESC
            """,
            (clean_rut,),
        ).fetchall()]


def mark_registry_alert(rut, summary=None):
    ensure_storage()
    clean_rut = clean_registry_rut(rut)
    if not clean_rut:
        return 0
    now = now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """
            UPDATE master_client_registry
            SET alert_count = alert_count + 1, last_alert_at = ?, last_alert_summary = ?
            WHERE clean_rut = ?
            """,
            (now, (summary or "")[:800], clean_rut),
        )
        return cur.rowcount


def registry_snapshot(limit=80):
    ensure_storage()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = [dict(row) for row in conn.execute(
            """
            SELECT * FROM master_client_registry
            ORDER BY
              CASE WHEN clean_rut = '' THEN 1 ELSE 0 END,
              clean_rut ASC,
              last_seen DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()]
        totals = dict(conn.execute(
            """
            SELECT
              COUNT(*) AS total,
              COUNT(DISTINCT CASE WHEN clean_rut <> '' THEN clean_rut END) AS unique_ruts,
              SUM(CASE WHEN source_module = 'erp' THEN 1 ELSE 0 END) AS erp,
              SUM(CASE WHEN source_module = 'diario_oficial' THEN 1 ELSE 0 END) AS diario_oficial,
              SUM(CASE WHEN source_module = 'inapi' THEN 1 ELSE 0 END) AS inapi,
              SUM(CASE WHEN alert_count > 0 THEN 1 ELSE 0 END) AS with_alerts
            FROM master_client_registry
            """
        ).fetchone())
    return {"rows": rows, "totals": totals}


def get_report(report_id):
    ensure_storage()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM do_ai_reports WHERE id = ?", (report_id,)).fetchone()
    return dict(row) if row else None


def dashboard_snapshot(limit=25, module=None):
    ensure_storage()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        if module:
            reports = [dict(row) for row in conn.execute(
                "SELECT * FROM do_ai_reports WHERE module = ? ORDER BY created_at DESC LIMIT ?",
                (module, limit),
            ).fetchall()]
            totals = conn.execute(
                """
                SELECT
                  COUNT(*) AS total_reports,
                  SUM(CASE WHEN urgency IN ('alto','critico') THEN 1 ELSE 0 END) AS high_risk,
                  COUNT(DISTINCT source_hash) AS unique_sources
                FROM do_ai_reports
                WHERE module = ?
                """,
                (module,),
            ).fetchone()
        else:
            reports = [dict(row) for row in conn.execute(
                "SELECT * FROM do_ai_reports ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()]
            totals = conn.execute(
                """
                SELECT
                  COUNT(*) AS total_reports,
                  SUM(CASE WHEN urgency IN ('alto','critico') THEN 1 ELSE 0 END) AS high_risk,
                  COUNT(DISTINCT source_hash) AS unique_sources
                FROM do_ai_reports
                """
            ).fetchone()
        memory = [dict(row) for row in conn.execute(
            "SELECT * FROM do_client_memory ORDER BY last_seen DESC LIMIT ?",
            (limit,),
        ).fetchall()]
    return {
        "reports": reports,
        "memory": memory,
        "totals": dict(totals),
    }

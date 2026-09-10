import csv
import hashlib
import io
import json
import os
import re
import sqlite3
import unicodedata
from datetime import datetime
from urllib.parse import quote

import requests


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "geointel_sales_radar.sqlite3")
DO_HISTORICO_DB = os.path.join(DATA_DIR, "do_historico.db")
AUDIT_REGISTRY_PATH = os.path.join(
    BASE_DIR,
    "quantus_data_opportunities_audit",
    "outputs",
    "source_registry_corrected.json",
)
FALLBACK_AUDIT_REGISTRY_PATH = os.path.join(
    BASE_DIR,
    "quantus_data_opportunities_audit",
    "outputs",
    "source_registry.json",
)

COMPANY_PATTERN = re.compile(
    r"\b(SPA|S\.P\.A\.?|S\.A\.?|SA|LIMITADA|LTDA\.?|SOCIEDAD ANONIMA)\b",
    re.IGNORECASE,
)
PERSONAL_RISK_PATTERN = re.compile(
    r"\b(E\.?I\.?R\.?L\.?|EMPRESA INDIVIDUAL|PERSONA NATURAL)\b",
    re.IGNORECASE,
)
CVE_PATTERN = re.compile(r"\s*\(CVE:\s*\d+\)\s*$", re.IGNORECASE)
CKAN_PACKAGE_SEARCH = "https://datos.gob.cl/api/3/action/package_search"

COMMUNES = [
    "Santiago",
    "Providencia",
    "Las Condes",
    "Vitacura",
    "Nunoa",
    "Maipu",
    "Puente Alto",
    "Rancagua",
    "Valparaiso",
    "Vina del Mar",
    "Concepcion",
    "Temuco",
    "Antofagasta",
    "La Serena",
    "Puerto Montt",
]


def _now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _connect():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_storage():
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS geointel_sources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source_kind TEXT NOT NULL,
                official_url TEXT,
                audit_decision TEXT NOT NULL,
                technical_status TEXT NOT NULL,
                privacy_status TEXT NOT NULL,
                legal_basis TEXT,
                use_category TEXT,
                notes TEXT,
                last_checked_at TEXT,
                last_error TEXT,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS geointel_leads (
                id TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                rubro TEXT NOT NULL,
                comuna TEXT NOT NULL,
                region TEXT NOT NULL,
                event_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_url TEXT NOT NULL,
                source_date TEXT,
                evidence_text TEXT,
                score INTEGER NOT NULL,
                score_reasons TEXT NOT NULL,
                technical_status TEXT NOT NULL,
                privacy_status TEXT NOT NULL,
                commercial_status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(normalized_name, source_url)
            );

            CREATE TABLE IF NOT EXISTS geointel_runs (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                records_found INTEGER NOT NULL DEFAULT 0,
                records_saved INTEGER NOT NULL DEFAULT 0,
                records_blocked INTEGER NOT NULL DEFAULT 0,
                detail TEXT
            );

            CREATE TABLE IF NOT EXISTS geointel_market_signals (
                id TEXT PRIMARY KEY,
                signal_type TEXT NOT NULL,
                rubro TEXT NOT NULL,
                comuna TEXT NOT NULL,
                period TEXT NOT NULL,
                metric_value INTEGER NOT NULL,
                comparison_value INTEGER,
                growth_pct REAL,
                source_id TEXT NOT NULL,
                evidence_text TEXT,
                technical_status TEXT NOT NULL,
                privacy_status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(signal_type, rubro, comuna, period, source_id)
            );
            """
        )
    seed_sources()


def _load_audit_sources():
    path = AUDIT_REGISTRY_PATH if os.path.exists(AUDIT_REGISTRY_PATH) else FALLBACK_AUDIT_REGISTRY_PATH
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _source_status(item):
    decision = (item.get("decision") or "PARTIAL").upper()
    has_pn = bool(item.get("has_pn"))
    use_category = item.get("use_category") or item.get("commercial_use") or ""
    if has_pn and decision != "PASS":
        return "BLOCK", "APTO SOLO CON FILTRO PJ", "Contiene posible persona natural; no se activa sin filtro juridico."
    if "Solo Analisis Agregado" in use_category or "SOLO AGREGADO" in (item.get("compliance_status") or ""):
        return "BLOCK", "SOLO AGREGADO", "No puede generar leads individuales."
    if decision == "PASS":
        return "PASS", "B2B NO PERSONAL", "Fuente auditada como recuperable y de bajo riesgo para empresas."
    return "PARTIAL", "REQUIERE CONTROL", "Fuente usable solo con controles o piloto."


def seed_sources():
    ensure = [
        {
            "id": "do_historico_empresas",
            "name": "Diario Oficial historico local - Empresas y Cooperativas",
            "source_kind": "sqlite_local",
            "official_url": "https://www.diariooficial.interior.gob.cl/",
            "audit_decision": "PASS",
            "technical_status": "PASS" if os.path.exists(DO_HISTORICO_DB) else "BLOCK",
            "privacy_status": "B2B NO PERSONAL",
            "legal_basis": "Publicaciones oficiales; uso interno B2B con exclusion de EIRL/personas naturales.",
            "use_category": "Inteligencia Comercial Interna",
            "notes": "Extractor activo inicial. Filtra sociedades y bloquea EIRL/persona natural.",
        },
        {
            "id": "datos_gob_patentes_municipales",
            "name": "Datos.gob.cl - Patentes municipales",
            "source_kind": "ckan_csv",
            "official_url": "https://datos.gob.cl/dataset?q=patentes+municipales",
            "audit_decision": "PARTIAL",
            "technical_status": "PARTIAL",
            "privacy_status": "APTO SOLO CON FILTRO PJ",
            "legal_basis": "Transparencia activa municipal Ley 20.285; uso interno con filtro estricto de personas juridicas.",
            "use_category": "Inteligencia Comercial Interna ERP/POS",
            "notes": "Extractor activo con filtro PJ. Bloquea personas naturales y filas sin razon social empresarial.",
        },
        {
            "id": "sii_empresas_activas",
            "name": "SII - Empresas activas, apertura/cierre y rubros",
            "source_kind": "official_pending",
            "official_url": "https://www.sii.cl/sobre_el_sii/datos_abiertos.html",
            "audit_decision": "PARTIAL",
            "technical_status": "BLOCK",
            "privacy_status": "APTO SOLO CON FILTRO PJ / AGREGADO",
            "legal_basis": "Datos abiertos SII; pendiente localizar dataset oficial descargable y filtro PJ.",
            "use_category": "Inteligencia Comercial Interna ERP/POS",
            "notes": "No se activa hasta tener dataset oficial reproducible. Evita inventar SII.",
        }
    ]
    for item in _load_audit_sources():
        sid = f"audit_{int(item.get('id') or 0):02d}"
        technical, privacy, notes = _source_status(item)
        ensure.append(
            {
                "id": sid,
                "name": item.get("name") or item.get("source") or sid,
                "source_kind": "audited_registry",
                "official_url": item.get("url") or item.get("test_url"),
                "audit_decision": (item.get("decision") or "PARTIAL").upper(),
                "technical_status": technical,
                "privacy_status": privacy,
                "legal_basis": item.get("legal_basis") or "",
                "use_category": item.get("use_category") or item.get("commercial_use") or "",
                "notes": notes,
            }
        )

    with _connect() as conn:
        for source in ensure:
            conn.execute(
                """
                INSERT INTO geointel_sources (
                    id, name, source_kind, official_url, audit_decision, technical_status,
                    privacy_status, legal_basis, use_category, notes, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    source_kind=excluded.source_kind,
                    official_url=excluded.official_url,
                    audit_decision=excluded.audit_decision,
                    technical_status=CASE
                        WHEN geointel_sources.last_checked_at IS NOT NULL THEN geointel_sources.technical_status
                        ELSE excluded.technical_status
                    END,
                    privacy_status=excluded.privacy_status,
                    legal_basis=excluded.legal_basis,
                    use_category=excluded.use_category,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at
                """,
                (
                    source["id"],
                    source["name"],
                    source["source_kind"],
                    source.get("official_url"),
                    source["audit_decision"],
                    source["technical_status"],
                    source["privacy_status"],
                    source.get("legal_basis"),
                    source.get("use_category"),
                    source.get("notes"),
                    _now(),
                ),
            )


def _clean_company_name(title):
    text = CVE_PATTERN.sub("", title or "").strip(" .-")
    text = re.sub(r"^Solicitud numero\s+\d+-\d+\.-\s*", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def _normalize(text):
    return re.sub(r"[^A-Z0-9]+", " ", (text or "").upper()).strip()


def _strip_accents(text):
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text or "") if not unicodedata.combining(ch)
    )


def _norm_key(text):
    return re.sub(r"[^a-z0-9]+", "_", _strip_accents(text or "").lower()).strip("_")


def _pick(row, *needles):
    normalized = {_norm_key(key): value for key, value in row.items()}
    for key, value in normalized.items():
        if all(needle in key for needle in needles):
            return (value or "").strip()
    return ""


def _rut_is_company(rut):
    digits = re.sub(r"[^0-9Kk]", "", rut or "")
    if len(digits) < 3:
        return False
    number = re.sub(r"[^0-9]", "", digits[:-1] or digits)
    try:
        return int(number) >= 50000000
    except ValueError:
        return False


def _is_company_name(name):
    return bool(COMPANY_PATTERN.search(name or "")) and not bool(PERSONAL_RISK_PATTERN.search(name or ""))


def _source_date_from_dataset(dataset):
    return (
        dataset.get("metadata_modified")
        or dataset.get("metadata_created")
        or datetime.now().strftime("%Y-%m-%d")
    )[:10]


def _download_csv_rows(url, max_rows):
    response = requests.get(url, timeout=30, headers={"User-Agent": "QuantusGeoIntel/1.0"})
    response.raise_for_status()
    raw = response.content
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", errors="replace")
    sample = text[:4096]
    dialect = csv.Sniffer().sniff(sample, delimiters=";,")
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    rows = []
    for index, row in enumerate(reader):
        if index >= max_rows:
            break
        rows.append(row)
    return rows


def _classify_rubro(name, text):
    haystack = f"{name} {text}".upper()
    rules = [
        ("Inmobiliaria", ["INMOBILIARIA", "CORRETAJE", "PROPIEDAD"]),
        ("Construccion", ["CONSTRUCTORA", "CONSTRUCCION", "INGENIERIA"]),
        ("Comercio", ["COMERCIAL", "COMERCIALIZADORA", "DISTRIBUIDORA"]),
        ("Transporte y logistica", ["TRANSPORTE", "LOGISTIC", "LOGISTICA"]),
        ("Salud y belleza", ["SALUD", "ESTETICA", "DROGUERIA", "CLINICA"]),
        ("Gastronomia", ["GASTRONOM", "RESTAURANT", "ALIMENT"]),
        ("Industrial", ["INDUSTRIAL", "MAESTRANZA", "FORESTAL", "AGRICOLA"]),
        ("Tecnologia y servicios", ["TECNOLOG", "SOFTWARE", "SERVICIOS"]),
    ]
    for rubro, keywords in rules:
        if any(keyword in haystack for keyword in keywords):
            return rubro
    return "Servicios empresariales"


def _infer_comuna(text):
    normalized = _normalize(text)
    for commune in COMMUNES:
        if _normalize(commune) in normalized:
            return commune
    return "No detectada"


def _infer_region(comuna):
    if comuna in {"Santiago", "Providencia", "Las Condes", "Vitacura", "Nunoa", "Maipu", "Puente Alto"}:
        return "Metropolitana"
    if comuna == "Rancagua":
        return "O'Higgins"
    if comuna in {"Valparaiso", "Vina del Mar"}:
        return "Valparaiso"
    if comuna == "Concepcion":
        return "Biobio"
    if comuna == "Temuco":
        return "La Araucania"
    if comuna == "Antofagasta":
        return "Antofagasta"
    if comuna == "La Serena":
        return "Coquimbo"
    if comuna == "Puerto Montt":
        return "Los Lagos"
    return "No detectada"


def _event_type(title, text):
    haystack = f"{title} {text}".upper()
    if "CONSTITUC" in haystack:
        return "Constitucion reciente"
    if "MODIFIC" in haystack:
        return "Modificacion societaria"
    if "DISOLUC" in haystack or "TERMINO" in haystack:
        return "Termino o disolucion"
    return "Publicacion societaria"


def _score(name, rubro, event_type, comuna):
    score = 42
    reasons = ["Base B2B por sociedad juridica en fuente oficial"]
    if event_type == "Constitucion reciente":
        score += 24
        reasons.append("Constitucion reciente")
    elif event_type == "Modificacion societaria":
        score += 14
        reasons.append("Movimiento societario")
    elif event_type == "Patente municipal activa":
        score += 20
        reasons.append("Negocio con patente municipal activa")
    if rubro in {"Comercio", "Gastronomia", "Salud y belleza", "Transporte y logistica", "Construccion"}:
        score += 18
        reasons.append(f"Rubro natural para ERP/POS Quantus: {rubro}")
    if comuna != "No detectada":
        score += 6
        reasons.append(f"Comuna identificada: {comuna}")
    if "SPA" in name.upper() or "S.A" in name.upper() or "LIMITADA" in name.upper():
        score += 8
        reasons.append("Tipo societario compatible con prospeccion no personal")
    return min(score, 100), reasons


def _lead_id(normalized_name, source_url):
    digest = hashlib.sha256(f"{normalized_name}|{source_url}".encode("utf-8")).hexdigest()[:16]
    return f"GEO-{digest.upper()}"


def _evidence_fragment(company_name, title, text):
    clean_title = re.sub(r"\s+", " ", title or "").strip()
    clean_text = re.sub(r"\s+", " ", text or "").strip()
    marker = company_name.split(" ")[0].upper() if company_name else ""
    upper_text = clean_text.upper()
    if marker and marker in upper_text:
        start = max(0, upper_text.find(marker) - 80)
        fragment = clean_text[start:start + 520].strip()
    else:
        fragment = clean_text[:420]
    if fragment:
        return f"{clean_title} | {fragment}"[:620]
    return clean_title[:620]


def run_do_extraction(limit=250):
    ensure_storage()
    run_id = f"RUN-DO-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    started = _now()
    found = 0
    saved = 0
    blocked = 0
    detail = ""
    with _connect() as conn:
        conn.execute(
            "INSERT INTO geointel_runs (id, source_id, status, started_at) VALUES (?, ?, ?, ?)",
            (run_id, "do_historico_empresas", "RUNNING", started),
        )
    try:
        if not os.path.exists(DO_HISTORICO_DB):
            raise RuntimeError(f"No existe base historica: {DO_HISTORICO_DB}")
        with sqlite3.connect(DO_HISTORICO_DB) as source_conn, _connect() as conn:
            source_conn.row_factory = sqlite3.Row
            rows = source_conn.execute(
                """
                SELECT fecha, seccion, url, titulo, texto
                FROM publicaciones
                WHERE seccion = 'Empresas y Cooperativas'
                ORDER BY fecha DESC, id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
            for row in rows:
                title = row["titulo"] or ""
                text = row["texto"] or ""
                if not COMPANY_PATTERN.search(title):
                    continue
                found += 1
                if PERSONAL_RISK_PATTERN.search(title):
                    blocked += 1
                    continue
                company_name = _clean_company_name(title)
                normalized = _normalize(company_name)
                if not normalized:
                    continue
                rubro = _classify_rubro(company_name, text)
                comuna = _infer_comuna(text)
                region = _infer_region(comuna)
                event = _event_type(title, text)
                score, reasons = _score(company_name, rubro, event, comuna)
                evidence = _evidence_fragment(company_name, title, text)
                lead_id = _lead_id(normalized, row["url"])
                cur = conn.execute(
                    """
                    INSERT INTO geointel_leads (
                        id, company_name, normalized_name, rubro, comuna, region,
                        event_type, source_id, source_name, source_url, source_date,
                        evidence_text, score, score_reasons, technical_status,
                        privacy_status, commercial_status, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(normalized_name, source_url) DO UPDATE SET
                        rubro=excluded.rubro,
                        comuna=excluded.comuna,
                        region=excluded.region,
                        event_type=excluded.event_type,
                        evidence_text=excluded.evidence_text,
                        score=excluded.score,
                        score_reasons=excluded.score_reasons,
                        technical_status=excluded.technical_status,
                        privacy_status=excluded.privacy_status,
                        commercial_status=excluded.commercial_status,
                        updated_at=excluded.updated_at
                    """,
                    (
                        lead_id,
                        company_name,
                        normalized,
                        rubro,
                        comuna,
                        region,
                        event,
                        "do_historico_empresas",
                        "Diario Oficial historico local",
                        row["url"],
                        row["fecha"],
                        evidence,
                        score,
                        json.dumps(reasons, ensure_ascii=False),
                        "PASS",
                        "B2B NO PERSONAL",
                        "OBSERVE_ONLY",
                        _now(),
                        _now(),
                    ),
                )
                if cur.rowcount:
                    saved += 1
            detail = f"Extraccion local DO: {len(rows)} publicaciones revisadas; EIRL/persona natural bloqueadas: {blocked}."
            conn.execute(
                """
                UPDATE geointel_sources
                SET technical_status=?, last_checked_at=?, last_error=NULL, updated_at=?
                WHERE id='do_historico_empresas'
                """,
                ("PASS" if saved else "BLOCK", _now(), _now()),
            )
    except Exception as exc:
        detail = str(exc)
        with _connect() as conn:
            conn.execute(
                """
                UPDATE geointel_sources
                SET technical_status='BLOCK', last_checked_at=?, last_error=?, updated_at=?
                WHERE id='do_historico_empresas'
                """,
                (_now(), detail[:500], _now()),
            )
            conn.execute(
                """
                UPDATE geointel_runs
                SET status='BLOCK', finished_at=?, records_found=?, records_saved=?, records_blocked=?, detail=?
                WHERE id=?
                """,
                (_now(), found, saved, blocked, detail[:1000], run_id),
            )
        return {"ok": False, "run_id": run_id, "detail": detail, "found": found, "saved": saved, "blocked": blocked}

    with _connect() as conn:
        conn.execute(
            """
            UPDATE geointel_runs
            SET status='PASS', finished_at=?, records_found=?, records_saved=?, records_blocked=?, detail=?
            WHERE id=?
            """,
            (_now(), found, saved, blocked, detail, run_id),
        )
    return {"ok": True, "run_id": run_id, "detail": detail, "found": found, "saved": saved, "blocked": blocked}


def _upsert_patent_market_signals(conn, source_id):
    rows = conn.execute(
        """
        SELECT rubro, comuna, COUNT(*) AS total
        FROM geointel_leads
        WHERE source_id=?
        GROUP BY rubro, comuna
        """,
        (source_id,),
    ).fetchall()
    period = datetime.now().strftime("%Y-%m")
    for row in rows:
        signal_id = hashlib.sha256(
            f"patentes_activas|{row['rubro']}|{row['comuna']}|{period}|{source_id}".encode("utf-8")
        ).hexdigest()[:18]
        conn.execute(
            """
            INSERT INTO geointel_market_signals (
                id, signal_type, rubro, comuna, period, metric_value, comparison_value,
                growth_pct, source_id, evidence_text, technical_status, privacy_status,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(signal_type, rubro, comuna, period, source_id) DO UPDATE SET
                metric_value=excluded.metric_value,
                evidence_text=excluded.evidence_text,
                technical_status=excluded.technical_status,
                privacy_status=excluded.privacy_status,
                updated_at=excluded.updated_at
            """,
            (
                f"SIG-{signal_id.upper()}",
                "Rubros por comuna",
                row["rubro"],
                row["comuna"],
                period,
                row["total"],
                source_id,
                f"{row['total']} empresas juridicas con patente municipal activa clasificadas en {row['rubro']} / {row['comuna']}.",
                "PASS",
                "AGREGADO NO PERSONAL",
                _now(),
                _now(),
            ),
        )


def run_patentes_municipales_extraction(max_resources=4, max_rows_per_resource=1200):
    ensure_storage()
    run_id = f"RUN-PAT-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    source_id = "datos_gob_patentes_municipales"
    found = 0
    saved = 0
    blocked = 0
    detail = ""
    with _connect() as conn:
        conn.execute(
            "INSERT INTO geointel_runs (id, source_id, status, started_at) VALUES (?, ?, ?, ?)",
            (run_id, source_id, "RUNNING", _now()),
        )
    try:
        response = requests.get(
            CKAN_PACKAGE_SEARCH,
            params={"q": "patentes municipales", "rows": 12, "sort": "metadata_modified desc"},
            timeout=25,
            headers={"User-Agent": "QuantusGeoIntel/1.0"},
        )
        response.raise_for_status()
        payload = response.json()
        datasets = payload.get("result", {}).get("results", [])
        resources = []
        for dataset in datasets:
            org_title = ((dataset.get("organization") or {}).get("title") or "").replace("Municipalidad de ", "")
            for resource in dataset.get("resources") or []:
                fmt = (resource.get("format") or "").lower()
                url = resource.get("url") or resource.get("original_url")
                if url and "csv" in fmt:
                    resources.append((dataset, resource, org_title or "No detectada", url))
                if len(resources) >= int(max_resources):
                    break
            if len(resources) >= int(max_resources):
                break
        if not resources:
            raise RuntimeError("datos.gob.cl no devolvio recursos CSV de patentes municipales.")

        with _connect() as conn:
            for dataset, resource, comuna_hint, url in resources:
                rows = _download_csv_rows(url, int(max_rows_per_resource))
                source_date = _source_date_from_dataset(dataset)
                for row in rows:
                    found += 1
                    company_name = (
                        _pick(row, "raz", "social")
                        or _pick(row, "titular")
                        or _pick(row, "nombre")
                    ).strip(" ;")
                    rut = _pick(row, "rut")
                    activity = (
                        _pick(row, "activ", "principal")
                        or _pick(row, "giro")
                        or _pick(row, "actividad")
                        or _pick(row, "tipo", "patente")
                    )
                    patente_type = _pick(row, "tipo", "patente") or "Patente municipal"
                    comuna = comuna_hint.strip() or _infer_comuna(" ".join(row.values()))
                    if not company_name or PERSONAL_RISK_PATTERN.search(company_name):
                        blocked += 1
                        continue
                    if not (_rut_is_company(rut) or _is_company_name(company_name)):
                        blocked += 1
                        continue
                    normalized = _normalize(company_name)
                    rubro = _classify_rubro(company_name, activity)
                    region = _infer_region(comuna)
                    event = "Patente municipal activa"
                    score, reasons = _score(company_name, rubro, event, comuna)
                    reasons.append("Fuente municipal via datos.gob.cl")
                    if rut:
                        reasons.append("RUT empresa validado por rango juridico" if _rut_is_company(rut) else "Tipo societario validado por razon social")
                    source_url = f"{url}#rol={quote(_pick(row, 'rol') or normalized[:24])}"
                    lead_id = _lead_id(normalized, source_url)
                    evidence = (
                        f"{dataset.get('title')} | {company_name} | {patente_type.strip()} | "
                        f"{activity.strip()} | comuna {comuna}"
                    )[:620]
                    cur = conn.execute(
                        """
                        INSERT INTO geointel_leads (
                            id, company_name, normalized_name, rubro, comuna, region,
                            event_type, source_id, source_name, source_url, source_date,
                            evidence_text, score, score_reasons, technical_status,
                            privacy_status, commercial_status, created_at, updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(normalized_name, source_url) DO UPDATE SET
                            rubro=excluded.rubro,
                            comuna=excluded.comuna,
                            region=excluded.region,
                            event_type=excluded.event_type,
                            evidence_text=excluded.evidence_text,
                            score=excluded.score,
                            score_reasons=excluded.score_reasons,
                            technical_status=excluded.technical_status,
                            privacy_status=excluded.privacy_status,
                            commercial_status=excluded.commercial_status,
                            updated_at=excluded.updated_at
                        """,
                        (
                            lead_id,
                            company_name,
                            normalized,
                            rubro,
                            comuna,
                            region,
                            event,
                            source_id,
                            dataset.get("title") or "Patentes municipales datos.gob.cl",
                            source_url,
                            source_date,
                            evidence,
                            score,
                            json.dumps(reasons, ensure_ascii=False),
                            "PASS",
                            "B2B NO PERSONAL",
                            "OBSERVE_ONLY",
                            _now(),
                            _now(),
                        ),
                    )
                    if cur.rowcount:
                        saved += 1
            _upsert_patent_market_signals(conn, source_id)
            existing_leads = conn.execute(
                "SELECT COUNT(*) AS total FROM geointel_leads WHERE source_id=?",
                (source_id,),
            ).fetchone()["total"]
            conn.execute(
                """
                UPDATE geointel_sources
                SET technical_status=?, last_checked_at=?, last_error=NULL, updated_at=?
                WHERE id=?
                """,
                ("PASS" if (saved or existing_leads) else "BLOCK", _now(), _now(), source_id),
            )
        detail = (
            f"Patentes municipales datos.gob.cl: {len(resources)} recursos CSV, "
            f"{found} filas revisadas, {saved} leads PJ guardados, {blocked} filas bloqueadas por filtro no personal."
        )
    except Exception as exc:
        detail = str(exc)
        with _connect() as conn:
            conn.execute(
                """
                UPDATE geointel_sources
                SET technical_status='BLOCK', last_checked_at=?, last_error=?, updated_at=?
                WHERE id=?
                """,
                (_now(), detail[:500], _now(), source_id),
            )
            conn.execute(
                """
                UPDATE geointel_runs
                SET status='BLOCK', finished_at=?, records_found=?, records_saved=?, records_blocked=?, detail=?
                WHERE id=?
                """,
                (_now(), found, saved, blocked, detail[:1000], run_id),
            )
        return {"ok": False, "run_id": run_id, "detail": detail, "found": found, "saved": saved, "blocked": blocked}

    with _connect() as conn:
        conn.execute(
            """
            UPDATE geointel_runs
            SET status='PASS', finished_at=?, records_found=?, records_saved=?, records_blocked=?, detail=?
            WHERE id=?
            """,
            (_now(), found, saved, blocked, detail, run_id),
        )
    return {"ok": True, "run_id": run_id, "detail": detail, "found": found, "saved": saved, "blocked": blocked}


def run_internal_sales_base_refresh():
    do_result = run_do_extraction(limit=450)
    patent_result = run_patentes_municipales_extraction(max_resources=4, max_rows_per_resource=1200)
    ok = bool(do_result.get("ok")) and bool(patent_result.get("ok"))
    return {"ok": ok, "diario_oficial": do_result, "patentes_municipales": patent_result}


def _where(filters):
    clauses = ["1=1"]
    params = []
    if filters.get("rubro"):
        clauses.append("rubro = ?")
        params.append(filters["rubro"])
    if filters.get("comuna"):
        clauses.append("comuna = ?")
        params.append(filters["comuna"])
    if filters.get("min_score"):
        clauses.append("score >= ?")
        params.append(int(filters["min_score"]))
    if filters.get("q"):
        clauses.append("(company_name LIKE ? OR rubro LIKE ? OR comuna LIKE ?)")
        needle = f"%{filters['q']}%"
        params.extend([needle, needle, needle])
    return " AND ".join(clauses), params


def get_dashboard(filters=None):
    ensure_storage()
    filters = filters or {}
    where, params = _where(filters)
    with _connect() as conn:
        leads = conn.execute(
            f"""
            SELECT * FROM geointel_leads
            WHERE {where}
            ORDER BY score DESC, source_date DESC, updated_at DESC
            LIMIT 300
            """,
            params,
        ).fetchall()
        sources = conn.execute(
            "SELECT * FROM geointel_sources ORDER BY technical_status DESC, audit_decision DESC, id"
        ).fetchall()
        runs = conn.execute(
            "SELECT * FROM geointel_runs ORDER BY started_at DESC LIMIT 12"
        ).fetchall()
        market_signals = conn.execute(
            """
            SELECT *
            FROM geointel_market_signals
            ORDER BY metric_value DESC, rubro, comuna
            LIMIT 40
            """
        ).fetchall()
        totals = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN score >= 80 THEN 1 ELSE 0 END) AS high_score,
                COUNT(DISTINCT rubro) AS rubros,
                COUNT(DISTINCT comuna) AS comunas
            FROM geointel_leads
            """
        ).fetchone()
        erp_pos = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM geointel_leads
            WHERE rubro IN ('Comercio','Gastronomia','Salud y belleza','Transporte y logistica','Construccion')
            """
        ).fetchone()
        rubros = [row["rubro"] for row in conn.execute("SELECT DISTINCT rubro FROM geointel_leads ORDER BY rubro")]
        comunas = [row["comuna"] for row in conn.execute("SELECT DISTINCT comuna FROM geointel_leads ORDER BY comuna")]
    parsed_leads = []
    for lead in leads:
        item = dict(lead)
        item["score_reasons_list"] = json.loads(item.get("score_reasons") or "[]")
        parsed_leads.append(item)
    source_rows = [dict(row) for row in sources]
    pass_count = sum(1 for row in source_rows if row["technical_status"] == "PASS")
    block_count = sum(1 for row in source_rows if row["technical_status"] == "BLOCK")
    production_gate = {
        "status": "BLOCK",
        "reason": "Produccion bloqueada hasta validar despliegue en LXC/staging y revisar acceso maestro en servidor.",
    }
    if (totals["total"] or 0) > 0 and pass_count > 0:
        production_gate["technical_evidence"] = "PASS local: hay leads reales con fuente y bitacora."
    return {
        "generated_at": _now(),
        "leads": parsed_leads,
        "sources": source_rows,
        "runs": [dict(row) for row in runs],
        "market_signals": [dict(row) for row in market_signals],
        "totals": dict(totals),
        "erp_pos_total": erp_pos["total"] or 0,
        "rubros": rubros,
        "comunas": comunas,
        "filters": filters,
        "source_pass_count": pass_count,
        "source_block_count": block_count,
        "production_gate": production_gate,
    }


def export_csv(filters=None):
    dashboard = get_dashboard(filters)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "empresa",
            "rubro",
            "comuna",
            "region",
            "evento",
            "score",
            "estado_tecnico",
            "estado_privacidad",
            "estado_comercial",
            "fecha_fuente",
            "fuente",
            "evidencia",
        ]
    )
    for lead in dashboard["leads"]:
        writer.writerow(
            [
                lead["id"],
                lead["company_name"],
                lead["rubro"],
                lead["comuna"],
                lead["region"],
                lead["event_type"],
                lead["score"],
                lead["technical_status"],
                lead["privacy_status"],
                lead["commercial_status"],
                lead["source_date"],
                lead["source_url"],
                lead["evidence_text"],
            ]
        )
    return output.getvalue()

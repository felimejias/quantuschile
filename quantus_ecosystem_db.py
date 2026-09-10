"""
quantus_ecosystem_db.py - Capa de Persistencia Canónica y Normalizada
Arquitectura: Tabla Maestra CLIENTES (Single Source of Truth) + Tablas Satélite.
Soporta SQLite transaccional local y PostgreSQL (quantus_control).
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime, date

SQLITE_DB_PATH = os.getenv("QUANTUS_ECOSYSTEM_DB", "/opt/quantus/portal/data/quantus_ecosystem.db")
os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)

def normalize_rut(rut: str) -> str:
    if not rut:
        return ""
    clean = rut.replace(".", "").replace("-", "").strip().upper()
    if len(clean) < 2:
        return clean
    body = clean[:-1]
    dv = clean[-1]
    formatted = f"{int(body):,}".replace(",", ".") + f"-{dv}"
    return formatted

def get_db_connection():
    # Siempre inicializar SQLite con WAL para máxima concurrencia y tolerancia a fallos
    conn = sqlite3.connect(SQLITE_DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn

def init_ecosystem_tables():
    conn = get_db_connection()
    c = conn.cursor()

    # 1. Tabla Maestra de Clientes
    c.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
        rut TEXT NOT NULL UNIQUE,
        tipo_persona TEXT NOT NULL DEFAULT 'natural',
        nombre_razon_social TEXT NOT NULL,
        correo_principal TEXT NOT NULL,
        celular_principal TEXT,
        direccion TEXT,
        comuna TEXT,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        estado TEXT DEFAULT 'activo'
    );
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_clientes_rut ON clientes(rut);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes(correo_principal);")

    # 2. Satélite: Diario Oficial
    c.execute("""
    CREATE TABLE IF NOT EXISTS susc_diario_oficial (
        id_suscripcion INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER NOT NULL,
        rut_monitoreado TEXT NOT NULL,
        ruts_adicionales TEXT,
        watch_targets_json TEXT,
        palabras_clave TEXT,
        plan TEXT NOT NULL,
        payment_mode TEXT DEFAULT 'one_time',
        estado TEXT DEFAULT 'pendiente_pago',
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
    );
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_susc_do_cliente ON susc_diario_oficial(id_cliente);")

    # 3. Satélite: Licitaciones Mercado Público
    c.execute("""
    CREATE TABLE IF NOT EXISTS susc_licitaciones (
        id_suscripcion INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER NOT NULL,
        rut_empresa TEXT NOT NULL,
        rubro TEXT,
        region_cobertura TEXT DEFAULT 'Nacional',
        monto_minimo TEXT DEFAULT 'todos',
        plan TEXT NOT NULL,
        payment_mode TEXT DEFAULT 'one_time',
        estado TEXT DEFAULT 'pendiente_pago',
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
    );
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_susc_lic_cliente ON susc_licitaciones(id_cliente);")

    # 4. Satélite: Marcas INAPI
    c.execute("""
    CREATE TABLE IF NOT EXISTS susc_marcas_inapi (
        id_suscripcion INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER NOT NULL,
        marca_monitoreada TEXT NOT NULL,
        tipo_marca TEXT DEFAULT 'denominativa',
        clase_niza TEXT,
        direccion_titular TEXT,
        comuna_titular TEXT,
        logo_path TEXT,
        logo_sha256 TEXT,
        poder_simple_path TEXT,
        inicio_act_path TEXT,
        plan TEXT DEFAULT 'registro_marca',
        estado TEXT DEFAULT 'pendiente_pago',
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
    );
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_susc_marcas_cliente ON susc_marcas_inapi(id_cliente);")

    # 5. Satélite: Remates Judiciales
    c.execute("""
    CREATE TABLE IF NOT EXISTS susc_remates (
        id_suscripcion INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER NOT NULL,
        region_interes TEXT DEFAULT 'Todo Chile',
        tipo_bien TEXT DEFAULT 'Todos los Bienes',
        monto_postura_minima TEXT,
        plan TEXT NOT NULL,
        monto INTEGER DEFAULT 29900,
        estado TEXT DEFAULT 'pendiente_pago',
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
    );
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_susc_remates_cliente ON susc_remates(id_cliente);")

    # 6. Satélite: Empleos Públicos
    c.execute("""
    CREATE TABLE IF NOT EXISTS susc_empleos_publicos (
        id_suscripcion INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER NOT NULL,
        cv_url TEXT,
        cv_sha256 TEXT,
        cv_size_bytes INTEGER,
        cargo_buscado TEXT,
        titulos TEXT,
        region_residencia TEXT,
        renta_minima INTEGER DEFAULT 0,
        estado TEXT DEFAULT 'activo',
        match_status TEXT DEFAULT 'pending_matching',
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
    );
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_susc_empleos_cliente ON susc_empleos_publicos(id_cliente);")

    # 7. Tabla Documentos Subidos (Auditoría Criptográfica)
    c.execute("""
    CREATE TABLE IF NOT EXISTS uploaded_documents (
        id_doc INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER,
        modulo TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_sha256 TEXT NOT NULL,
        mime_type TEXT,
        size_bytes INTEGER,
        scan_status TEXT DEFAULT 'clean',
        retention_days INTEGER DEFAULT 365,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
    );
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_docs_hash ON uploaded_documents(file_sha256);")

    # 8. Tabla Eventos de Auditoría (Trazabilidad ISO 27001 / 9001)
    c.execute("""
    CREATE TABLE IF NOT EXISTS audit_events (
        id_audit INTEGER PRIMARY KEY AUTOINCREMENT,
        actor TEXT NOT NULL,
        action TEXT NOT NULL,
        object_type TEXT NOT NULL,
        object_id TEXT,
        payload_json TEXT,
        ip_address TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_events(timestamp);")

    conn.commit()
    conn.close()

# Auto-inicializar al importar
init_ecosystem_tables()

def upsert_cliente(rut: str, nombre: str, email: str, telefono: str = "", tipo_persona: str = "natural", direccion: str = "", comuna: str = "") -> int:
    """Inserta o actualiza un cliente en la tabla maestra CLIENTES y retorna su id_cliente."""
    norm_rut = normalize_rut(rut)
    email_clean = (email or "").strip().lower()
    nombre_clean = (nombre or "").strip()
    tel_clean = (telefono or "").strip()

    if not norm_rut:
        norm_rut = f"TEMP-{hashlib.sha256(email_clean.encode()).hexdigest()[:10].upper()}"

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT id_cliente, nombre_razon_social, correo_principal, celular_principal, direccion, comuna FROM clientes WHERE rut = ?", (norm_rut,))
    row = c.fetchone()

    if row:
        id_cliente = row["id_cliente"]
        # Actualizar campos de contacto si vienen con valor
        c.execute("""
            UPDATE clientes 
            SET nombre_razon_social = COALESCE(NULLIF(?, ''), nombre_razon_social),
                correo_principal = COALESCE(NULLIF(?, ''), correo_principal),
                celular_principal = COALESCE(NULLIF(?, ''), celular_principal),
                direccion = COALESCE(NULLIF(?, ''), direccion),
                comuna = COALESCE(NULLIF(?, ''), comuna)
            WHERE id_cliente = ?
        """, (nombre_clean, email_clean, tel_clean, direccion, comuna, id_cliente))
    else:
        c.execute("""
            INSERT INTO clientes (rut, tipo_persona, nombre_razon_social, correo_principal, celular_principal, direccion, comuna, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'activo')
        """, (norm_rut, tipo_persona, nombre_clean, email_clean, tel_clean, direccion, comuna))
        id_cliente = c.lastrowid

    conn.commit()
    conn.close()
    return id_cliente

def save_susc_diario_oficial(id_cliente: int, rut_monitoreado: str, ruts_adicionales: str = "", watch_targets: list = None, plan: str = "anual", payment_mode: str = "one_time", estado: str = "pendiente_pago") -> int:
    conn = get_db_connection()
    c = conn.cursor()
    watch_json = json.dumps(watch_targets or [], ensure_ascii=False)
    c.execute("""
        INSERT INTO susc_diario_oficial (id_cliente, rut_monitoreado, ruts_adicionales, watch_targets_json, plan, payment_mode, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (id_cliente, normalize_rut(rut_monitoreado), ruts_adicionales, watch_json, plan, payment_mode, estado))
    susc_id = c.lastrowid
    conn.commit()
    conn.close()
    return susc_id

def save_susc_licitaciones(id_cliente: int, rut_empresa: str, rubro: str, region_cobertura: str = "Nacional", monto_minimo: str = "todos", plan: str = "pyme_pro", payment_mode: str = "one_time", estado: str = "pendiente_pago") -> int:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO susc_licitaciones (id_cliente, rut_empresa, rubro, region_cobertura, monto_minimo, plan, payment_mode, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (id_cliente, normalize_rut(rut_empresa), rubro, region_cobertura, monto_minimo, plan, payment_mode, estado))
    susc_id = c.lastrowid
    conn.commit()
    conn.close()
    return susc_id

def save_susc_marcas_inapi(id_cliente: int, marca: str, tipo_marca: str = "denominativa", clase_niza: str = "", direccion: str = "", comuna: str = "", logo_path: str = "", logo_sha256: str = "", poder_simple_path: str = "", inicio_act_path: str = "", plan: str = "registro_marca", estado: str = "pendiente_pago") -> int:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO susc_marcas_inapi (id_cliente, marca_monitoreada, tipo_marca, clase_niza, direccion_titular, comuna_titular, logo_path, logo_sha256, poder_simple_path, inicio_act_path, plan, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (id_cliente, marca, tipo_marca, clase_niza, direccion, comuna, logo_path, logo_sha256, poder_simple_path, inicio_act_path, plan, estado))
    susc_id = c.lastrowid
    conn.commit()
    conn.close()
    return susc_id

def save_susc_remates(id_cliente: int, region_interes: str = "Todo Chile", tipo_bien: str = "Todos los Bienes", monto_postura_minima: str = "", plan: str = "Plan Inversionista Mensual", monto: int = 29900, estado: str = "pendiente_pago") -> int:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO susc_remates (id_cliente, region_interes, tipo_bien, monto_postura_minima, plan, monto, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (id_cliente, region_interes, tipo_bien, monto_postura_minima, plan, monto, estado))
    susc_id = c.lastrowid
    conn.commit()
    conn.close()
    return susc_id

def save_susc_empleos_publicos(id_cliente: int, cv_url: str = "", cv_sha256: str = "", cv_size_bytes: int = 0, cargo_buscado: str = "", titulos: str = "", region_residencia: str = "Todo Chile", renta_minima: int = 0, estado: str = "activo") -> int:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO susc_empleos_publicos (id_cliente, cv_url, cv_sha256, cv_size_bytes, cargo_buscado, titulos, region_residencia, renta_minima, estado, match_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'parsed')
    """, (id_cliente, cv_url, cv_sha256, cv_size_bytes, cargo_buscado, titulos, region_residencia, renta_minima, estado))
    susc_id = c.lastrowid
    conn.commit()
    conn.close()
    return susc_id

def record_uploaded_doc(id_cliente: int, modulo: str, file_name: str, file_path: str, file_sha256: str, mime_type: str = "", size_bytes: int = 0) -> int:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO uploaded_documents (id_cliente, modulo, file_name, file_path, file_sha256, mime_type, size_bytes, scan_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'clean')
    """, (id_cliente, modulo, file_name, file_path, file_sha256, mime_type, size_bytes))
    doc_id = c.lastrowid
    conn.commit()
    conn.close()
    return doc_id

def record_audit_event(actor: str, action: str, object_type: str, object_id: str, payload: dict = None, ip_address: str = ""):
    conn = get_db_connection()
    c = conn.cursor()
    payload_str = json.dumps(payload or {}, ensure_ascii=False)
    c.execute("""
        INSERT INTO audit_events (actor, action, object_type, object_id, payload_json, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (actor, action, object_type, str(object_id), payload_str, ip_address))
    conn.commit()
    conn.close()


def record_payment(id_cliente: int, monto_clp: int, estado_transaccion: str, pasarela: str = "mercadopago", mp_payment_id: str = None, id_suscripcion: int = None, modulo: str = "diario_oficial", comprobante_url: str = "", raw_webhook: dict = None) -> int:
    conn = get_db_connection()
    c = conn.cursor()
    payload_str = json.dumps(raw_webhook or {}, ensure_ascii=False)
    c.execute('''
        INSERT INTO historial_pagos (id_cliente, id_suscripcion, modulo, pasarela, mp_payment_id, monto_clp, estado_transaccion, comprobante_url, raw_webhook_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (id_cliente, id_suscripcion, modulo, pasarela, mp_payment_id, monto_clp, estado_transaccion, comprobante_url, payload_str))
    pago_id = c.lastrowid
    conn.commit()
    conn.close()
    return pago_id

def create_expediente(id_cliente: int, modulo: str) -> str:
    conn = get_db_connection()
    c = conn.cursor()
    year = datetime.now().year
    c.execute("SELECT count(*) FROM expedientes")
    count = c.fetchone()[0] + 1
    folio = f"QCH-{year}-{count:06d}"
    c.execute('''
        INSERT INTO expedientes (folio, id_cliente, modulo, estado)
        VALUES (?, ?, ?, 'activo')
    ''', (folio, id_cliente, modulo))
    conn.commit()
    conn.close()
    return folio

def get_client_expedientes(id_cliente: int) -> list:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id_expediente, folio, modulo, estado, created_at FROM expedientes WHERE id_cliente = ? ORDER BY id_expediente DESC", (id_cliente,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_payment_history(id_cliente: int = None) -> list:
    conn = get_db_connection()
    c = conn.cursor()
    if id_cliente:
        c.execute("SELECT * FROM historial_pagos WHERE id_cliente = ? ORDER BY id_pago DESC", (id_cliente,))
    else:
        c.execute("SELECT * FROM historial_pagos ORDER BY id_pago DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_convenio_juridico(codigo: str) -> dict:
    if not codigo:
        return None
    codigo_clean = codigo.strip().upper()
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM convenios_juridicos WHERE UPPER(codigo) = ? AND activo = 1", (codigo_clean,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def create_convenio_juridico(codigo: str, nombre_estudio: str, dias: int = 30, abogado: str = "", correo: str = "") -> int:
    conn = get_db_connection()
    c = conn.cursor()
    codigo_clean = codigo.strip().upper()
    c.execute("""
        INSERT INTO convenios_juridicos (codigo, nombre_estudio, abogado_responsable, correo_contacto, dias_auditoria_retroactiva, activo)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (codigo_clean, nombre_estudio, abogado, correo, dias))
    cid = c.lastrowid
    conn.commit()
    conn.close()
    return cid

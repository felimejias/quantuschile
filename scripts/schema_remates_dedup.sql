-- Esquema de Persistencia e Idempotencia para Quantus Remates
-- Motor: PostgreSQL / SQLite (Multitenant & Trazable)

-- 1. Tabla Maestra de Remates Unificados (Clave Única Natural para Evitar Duplicados de Extracción)
CREATE TABLE IF NOT EXISTS remates_inmobiliarios (
    id VARCHAR(64) PRIMARY KEY, -- Hash SHA256 o ID Único
    dedup_hash VARCHAR(64) UNIQUE NOT NULL, -- HASH(rol_causa + tribunal_normalizado + fecha_subasta)
    
    tipo_propiedad VARCHAR(50) NOT NULL,
    direccion VARCHAR(255) NOT NULL,
    comuna VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    
    latitud NUMERIC(10, 7),
    longitud NUMERIC(10, 7),
    google_maps_url TEXT,
    
    tribunal VARCHAR(150) NOT NULL,
    rol_causa VARCHAR(50) NOT NULL,
    caratula VARCHAR(255),
    
    fecha_subasta TIMESTAMP NOT NULL,
    modalidad VARCHAR(50),
    
    minimo_clp BIGINT NOT NULL,
    minimo_uf NUMERIC(10, 2),
    garantia_monto_clp BIGINT,
    tasacion_mercado_estimada BIGINT,
    descuento_estimado_pct NUMERIC(5, 2),
    
    cbr_registro TEXT,
    fuente_origen VARCHAR(50) NOT NULL, -- 'DIARIO_OFICIAL', 'TGR', 'DICREP', 'PJUD'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de Envíos / Despachos a Usuarios (Garantía de Cero Spam / Cero Duplicados)
CREATE TABLE IF NOT EXISTS log_despachos_remates (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    remate_id VARCHAR(64) NOT NULL REFERENCES remates_inmobiliarios(id),
    canal VARCHAR(20) NOT NULL, -- 'WHATSAPP', 'EMAIL', 'PUSH', 'PORTAL'
    fecha_despacho TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraint Unico: Un usuario JAMÁS recibe la misma propiedad por el mismo canal más de una vez
    CONSTRAINT unique_user_remate_canal UNIQUE (user_id, remate_id, canal)
);

CREATE INDEX IF NOT EXISTS idx_remates_comuna ON remates_inmobiliarios(comuna);
CREATE INDEX IF NOT EXISTS idx_remates_fecha ON remates_inmobiliarios(fecha_subasta);

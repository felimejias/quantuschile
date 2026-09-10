-- =============================================================================
-- Quantus Marketing Center — Migración 001
-- Crea todas las tablas del módulo de marketing.
--
-- Base de datos: data/marketing.sqlite3 (separada de do_intelligence.sqlite3)
-- Fecha: 2026-08-05
-- Plan: implementation_plan.md v2, §4
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 4.1 — Campañas
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marketing_campaigns (
    id                  TEXT PRIMARY KEY,  -- UUID
    tenant_id           TEXT NOT NULL DEFAULT 'quantus',
    name                TEXT NOT NULL,
    service_category    TEXT NOT NULL,     -- 'diario_oficial','ley_21719','licitaciones','inapi','erp','remates'
    target_audience     TEXT,
    flow_type           TEXT NOT NULL,     -- 'ORGANIC','DIRECT','BOTH'
    status              TEXT NOT NULL DEFAULT 'DRAFT',
    created_by          TEXT NOT NULL,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime')),
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime'))
);

-- ---------------------------------------------------------------------------
-- 4.1 — Contenidos por canal
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marketing_contents (
    id                  TEXT PRIMARY KEY,
    campaign_id         TEXT NOT NULL REFERENCES marketing_campaigns(id),
    channel             TEXT NOT NULL,     -- 'instagram','facebook','linkedin','whatsapp_template','whatsapp_status','email'
    flow_type           TEXT NOT NULL,     -- 'ORGANIC' o 'DIRECT'
    content_type        TEXT NOT NULL,     -- 'post','story','reel','carousel','template','status','article'
    title               TEXT,
    body                TEXT NOT NULL,
    hashtags            TEXT,
    destination_url     TEXT,
    content_hash        TEXT NOT NULL,     -- SHA-256(body+channel+campaign_id)
    ai_model_used       TEXT,
    ai_generation_log   TEXT,             -- JSON serializado
    status              TEXT NOT NULL DEFAULT 'DRAFT',
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime')),
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_contents_campaign ON marketing_contents(campaign_id);
CREATE INDEX IF NOT EXISTS idx_contents_status ON marketing_contents(status);
CREATE INDEX IF NOT EXISTS idx_contents_hash ON marketing_contents(content_hash);

-- ---------------------------------------------------------------------------
-- 4.1 — Activos visuales
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marketing_assets (
    id                          TEXT PRIMARY KEY,
    content_id                  TEXT NOT NULL REFERENCES marketing_contents(id),
    asset_type                  TEXT NOT NULL,     -- 'image_1080x1350','image_1080x1920','image_1200x627','video','pdf','carousel_slide'
    file_path                   TEXT NOT NULL,
    alt_text                    TEXT NOT NULL,     -- Obligatorio WCAG 2.2 AA
    mime_type                   TEXT NOT NULL,
    file_size_bytes             INTEGER,
    visual_compliance_status    TEXT DEFAULT 'PENDING',  -- 'PENDING','PASS','BLOCKED'
    visual_compliance_log       TEXT,             -- JSON serializado
    created_at                  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_assets_content ON marketing_assets(content_id);

-- ---------------------------------------------------------------------------
-- 4.2 — Consentimiento (Opt-In)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marketing_consents (
    id                      TEXT PRIMARY KEY,
    tenant_id               TEXT NOT NULL DEFAULT 'quantus',
    contact_id              TEXT NOT NULL,
    channel                 TEXT NOT NULL,     -- 'whatsapp','email','sms'
    consent_status          TEXT NOT NULL,     -- 'ACTIVE','REVOKED','EXPIRED'
    consent_source          TEXT NOT NULL,     -- 'web_form','whatsapp_opt_in','manual_import','api'
    consent_text_version    TEXT NOT NULL,
    consented_at            TEXT NOT NULL,
    consent_ip              TEXT,
    consent_user_agent      TEXT,
    campaign_or_form_id     TEXT,
    evidence_reference      TEXT,
    legal_basis             TEXT NOT NULL,     -- 'consent','contractual_relationship','legitimate_interest'
    legal_basis_detail      TEXT,             -- 'Ley 19.628 + Política Meta'
    revoked_at              TEXT,
    revocation_source       TEXT,
    created_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_consents_contact ON marketing_consents(contact_id, channel);
CREATE INDEX IF NOT EXISTS idx_consents_status ON marketing_consents(consent_status);

-- ---------------------------------------------------------------------------
-- 4.3 — Lista de Supresión Global
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marketing_suppressions (
    id                  TEXT PRIMARY KEY,
    tenant_id           TEXT NOT NULL DEFAULT 'quantus',
    contact_id          TEXT,
    normalized_phone    TEXT,             -- E.164
    normalized_email    TEXT,             -- lowercase, trimmed
    channel             TEXT NOT NULL,     -- 'whatsapp','email','all'
    scope               TEXT NOT NULL,     -- 'campaign','channel','all_commercial','administrative_block'
    scope_campaign_id   TEXT,
    reason              TEXT NOT NULL,     -- 'opt_out_reply','opt_out_link','no_molestar','admin_block','complaint','invalid_contact','platform_block'
    source              TEXT NOT NULL,     -- 'user_reply','web_form','sernac','admin','meta_webhook','system'
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime')),
    expires_at          TEXT,
    revoked_at          TEXT,
    revocation_evidence TEXT,
    evidence_reference  TEXT,
    processed_by        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_suppressions_contact ON marketing_suppressions(contact_id);
CREATE INDEX IF NOT EXISTS idx_suppressions_phone ON marketing_suppressions(normalized_phone);
CREATE INDEX IF NOT EXISTS idx_suppressions_email ON marketing_suppressions(normalized_email);
CREATE INDEX IF NOT EXISTS idx_suppressions_channel ON marketing_suppressions(channel);

-- ---------------------------------------------------------------------------
-- 4.4 — Programación y Publicación
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marketing_schedules (
    id                  TEXT PRIMARY KEY,
    content_id          TEXT NOT NULL REFERENCES marketing_contents(id),
    flow_type           TEXT NOT NULL,
    channel             TEXT NOT NULL,
    external_account_id TEXT,
    scheduled_at        TEXT NOT NULL,
    idempotency_key     TEXT NOT NULL UNIQUE,
    content_hash        TEXT NOT NULL,
    published_at        TEXT,
    external_post_id    TEXT,
    status              TEXT NOT NULL DEFAULT 'SCHEDULED',
    retry_count         INTEGER DEFAULT 0,
    max_retries         INTEGER DEFAULT 3,
    last_error          TEXT,
    last_error_at       TEXT,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_schedules_content ON marketing_schedules(content_id);
CREATE INDEX IF NOT EXISTS idx_schedules_idempotency ON marketing_schedules(idempotency_key);
CREATE INDEX IF NOT EXISTS idx_schedules_status ON marketing_schedules(status);

-- ---------------------------------------------------------------------------
-- 4.5 — Aprobaciones y Cumplimiento
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marketing_approvals (
    id                      TEXT PRIMARY KEY,
    content_id              TEXT NOT NULL REFERENCES marketing_contents(id),
    compliance_status       TEXT NOT NULL,     -- 'PASS','WARNING','BLOCKED'
    compliance_checks       TEXT NOT NULL,     -- JSON: array de checks
    claims_validated        TEXT,             -- JSON: claims permitidos encontrados
    claims_blocked          TEXT,             -- JSON: claims bloqueados detectados
    visual_compliance       TEXT,             -- JSON
    approved_by             TEXT,
    approved_at             TEXT,
    approval_role           TEXT,
    rejection_reason        TEXT,
    changes_requested_log   TEXT,             -- JSON
    created_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_approvals_content ON marketing_approvals(content_id);

-- ---------------------------------------------------------------------------
-- 4.6 — CRM de Prospectos
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marketing_leads (
    id                  TEXT PRIMARY KEY,
    tenant_id           TEXT NOT NULL DEFAULT 'quantus',
    lead_name           TEXT,
    contact_phone       TEXT,
    contact_email       TEXT,
    company_name        TEXT,
    channel_origin      TEXT NOT NULL,
    interaction_type    TEXT NOT NULL,     -- 'interested','qualified_lead'
    campaign_id         TEXT REFERENCES marketing_campaigns(id),
    content_id          TEXT REFERENCES marketing_contents(id),
    utm_source          TEXT,
    utm_medium          TEXT,
    utm_campaign        TEXT,
    utm_content         TEXT,
    service_interest    TEXT,
    need_detected       TEXT,
    consent_id          TEXT REFERENCES marketing_consents(id),
    lead_status         TEXT NOT NULL DEFAULT 'NEW',
    assigned_agent      TEXT,
    followup_due_at     TEXT,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime')),
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_leads_campaign ON marketing_leads(campaign_id);
CREATE INDEX IF NOT EXISTS idx_leads_status ON marketing_leads(lead_status);

-- ---------------------------------------------------------------------------
-- 4.7 — Control de Frecuencia
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marketing_delivery_policies (
    id                          TEXT PRIMARY KEY,
    tenant_id                   TEXT NOT NULL DEFAULT 'quantus',
    channel                     TEXT NOT NULL,
    max_per_contact_per_day     INTEGER NOT NULL DEFAULT 1,
    max_per_contact_per_week    INTEGER NOT NULL DEFAULT 3,
    cooldown_hours_after_send   INTEGER NOT NULL DEFAULT 24,
    cooldown_hours_after_reject INTEGER NOT NULL DEFAULT 168,  -- 7 días
    blocked_hours_start         TEXT,         -- 'HH:MM'
    blocked_hours_end           TEXT,         -- 'HH:MM'
    no_duplicate_content_days   INTEGER NOT NULL DEFAULT 30,
    active                      INTEGER NOT NULL DEFAULT 1,    -- SQLite no tiene BOOLEAN
    created_at                  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime'))
);

CREATE TABLE IF NOT EXISTS marketing_delivery_log (
    id              TEXT PRIMARY KEY,
    contact_id      TEXT NOT NULL,
    channel         TEXT NOT NULL,
    content_id      TEXT NOT NULL,
    content_hash    TEXT NOT NULL,
    campaign_id     TEXT NOT NULL,
    sent_at         TEXT NOT NULL,
    policy_result   TEXT NOT NULL,     -- 'DELIVERY_POLICY_PASS','DELIVERY_POLICY_BLOCK'
    block_reason    TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_delivery_log_contact ON marketing_delivery_log(contact_id, channel);

-- ---------------------------------------------------------------------------
-- 4.8 — Métricas Comerciales
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marketing_metrics (
    id                          TEXT PRIMARY KEY,
    content_id                  TEXT REFERENCES marketing_contents(id),
    campaign_id                 TEXT REFERENCES marketing_campaigns(id),
    channel                     TEXT NOT NULL,
    impressions                 INTEGER DEFAULT 0,
    reach                       INTEGER DEFAULT 0,
    clicks                      INTEGER DEFAULT 0,
    landing_page_visits         INTEGER DEFAULT 0,
    form_submissions            INTEGER DEFAULT 0,
    whatsapp_conversations      INTEGER DEFAULT 0,
    qualified_leads             INTEGER DEFAULT 0,
    demonstrations_requested    INTEGER DEFAULT 0,
    proposals_created           INTEGER DEFAULT 0,
    customers_acquired          INTEGER DEFAULT 0,
    revenue_attributed_clp      INTEGER DEFAULT 0,  -- Enteros CLP (CARTA_MAGNA regla 9)
    measured_at                 TEXT NOT NULL,
    source                      TEXT NOT NULL,     -- 'meta_api','linkedin_api','manual','utm_tracking'
    confidence_level            TEXT,             -- 'exact','estimated','partial'
    created_at                  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_metrics_campaign ON marketing_metrics(campaign_id);

-- ---------------------------------------------------------------------------
-- 4.9 — Auditoría (una tabla por flujo)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marketing_organic_audit (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL DEFAULT 'quantus',
    actor       TEXT NOT NULL,
    actor_role  TEXT NOT NULL,
    action      TEXT NOT NULL,     -- 'CREATE','EDIT','APPROVE','REJECT','SCHEDULE','PUBLISH','CANCEL','ARCHIVE'
    entity_type TEXT NOT NULL,     -- 'campaign','content','asset','schedule'
    entity_id   TEXT NOT NULL,
    old_value   TEXT,             -- JSON
    new_value   TEXT,             -- JSON
    reason      TEXT,
    ip_address  TEXT,
    user_agent  TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime'))
);

CREATE TABLE IF NOT EXISTS marketing_direct_audit (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL DEFAULT 'quantus',
    actor       TEXT NOT NULL,
    actor_role  TEXT NOT NULL,
    action      TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id   TEXT NOT NULL,
    old_value   TEXT,
    new_value   TEXT,
    reason      TEXT,
    ip_address  TEXT,
    user_agent  TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime'))
);

-- ---------------------------------------------------------------------------
-- Políticas de frecuencia por defecto
-- ---------------------------------------------------------------------------
INSERT OR IGNORE INTO marketing_delivery_policies (id, tenant_id, channel, max_per_contact_per_day, max_per_contact_per_week, cooldown_hours_after_send, cooldown_hours_after_reject, blocked_hours_start, blocked_hours_end, no_duplicate_content_days)
VALUES
    ('default_whatsapp', 'quantus', 'whatsapp', 1, 2, 48, 168, '22:00', '08:00', 30),
    ('default_email', 'quantus', 'email', 1, 3, 24, 168, '23:00', '07:00', 30);

-- ---------------------------------------------------------------------------
-- Tabla de control de migraciones
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marketing_migrations (
    version     INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    applied_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime'))
);

INSERT OR IGNORE INTO marketing_migrations (version, name) VALUES (1, '001_create_marketing_tables');

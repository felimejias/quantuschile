#!/bin/bash
# ==============================================================================
# Quantus Chile SpA - Script de Respaldo Diario Inmutable y Rotación 30 Días
# Creado para cumplimiento de Continuidad Operacional y Ley 21.719
# ==============================================================================

set -euo pipefail

BACKUP_ROOT="/mnt/proyectos/felipe/backups"
APP_DIR="/mnt/proyectos/felipe/inapi_portal"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="quantus_snapshot_${TIMESTAMP}"
DEST_DIR="${BACKUP_ROOT}/${BACKUP_NAME}"
RETENTION_DAYS=30

echo "======================================================================"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando respaldo diario Quantus: ${BACKUP_NAME}"
echo "======================================================================"

mkdir -p "${DEST_DIR}"

# 1. Respaldar Bases de Datos SQLite en Caliente (usando .backup de sqlite3 para consistencia)
echo "[1/4] Respaldando bases de datos SQLite..."
mkdir -p "${DEST_DIR}/sqlite"

if [ -f "${APP_DIR}/data/do_historico.db" ]; then
    sqlite3 "${APP_DIR}/data/do_historico.db" ".backup '${DEST_DIR}/sqlite/do_historico.db'"
    echo "  ✓ do_historico.db respaldada"
fi

if [ -f "${APP_DIR}/empleos_publicos.db" ]; then
    sqlite3 "${APP_DIR}/empleos_publicos.db" ".backup '${DEST_DIR}/sqlite/empleos_publicos.db'"
    echo "  ✓ empleos_publicos.db respaldada"
fi

if [ -f "${APP_DIR}/data/communications_log.db" ]; then
    sqlite3 "${APP_DIR}/data/communications_log.db" ".backup '${DEST_DIR}/sqlite/communications_log.db'"
    echo "  ✓ communications_log.db respaldada"
fi

# 2. Respaldar datos críticos de configuración, personas y solicitudes ARCOP
echo "[2/4] Respaldando registros de auditoría y JSONs de estado..."
mkdir -p "${DEST_DIR}/data_state"

for f in do_people.json data/arcop_solicitudes.json data/purged_accounts_ledger.json data/clientes; do
    if [ -e "${APP_DIR}/${f}" ]; then
        cp -r "${APP_DIR}/${f}" "${DEST_DIR}/data_state/" || true
        echo "  ✓ ${f} respaldado"
    fi
done

# 3. Empaquetar y Generar Sello Criptográfico SHA-256
echo "[3/4] Empaquetando y sellando criptográficamente..."
cd "${BACKUP_ROOT}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
rm -rf "${BACKUP_NAME}"
sha256sum "${BACKUP_NAME}.tar.gz" > "${BACKUP_NAME}.sha256"

echo "  ✓ Archivo generado: ${BACKUP_ROOT}/${BACKUP_NAME}.tar.gz"
echo "  ✓ Sello SHA-256: $(cat "${BACKUP_ROOT}/${BACKUP_NAME}.sha256" | cut -d' ' -f1)"

# 4. Rotación: Eliminar respaldos con más de 30 días de antigüedad
echo "[4/4] Aplicando política de retención (${RETENTION_DAYS} días)..."
find "${BACKUP_ROOT}" -name "quantus_snapshot_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete || true
find "${BACKUP_ROOT}" -name "quantus_snapshot_*.sha256" -type f -mtime +${RETENTION_DAYS} -delete || true

echo "======================================================================"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Respaldo completado con éxito."
echo "======================================================================"

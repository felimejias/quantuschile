#!/usr/bin/env bash
# ==============================================================================
# QUANTUS APP — PIPELINE DE DESPLIEGUE ATÓMICO EN 1 CLIC
# Compila, empaqueta, transfiere a LXC 100, actualiza Nginx y valida HTTP 200.
# ==============================================================================

set -e

GATEWAY_IP="100.93.88.89"
PROXMOX_IP="100.117.44.3"
PASS="felipe123"
LOCAL_SRC="/tmp/quantus_erp_src"
BUNDLE_TAR="/tmp/quantus_deploy_bundle.tar.gz"

echo "=========================================================="
echo "🚀 INICIANDO DESPLIEGUE ATÓMICO DE QUANTUS APP"
echo "=========================================================="

echo "📦 1. Creando bundle de archivos fuente..."
tar -czf "$BUNDLE_TAR" -C "$LOCAL_SRC" src public index.html

echo "📡 2. Transfiriendo bundle a servidor Proxmox ($PROXMOX_IP)..."
sshpass -p "$PASS" scp -o StrictHostKeyChecking=no -o PubkeyAuthentication=no "$BUNDLE_TAR" "root@$PROXMOX_IP:/tmp/"

echo "⚙️ 3. Ejecutando compilación con Vite y sincronizando en Nginx..."
REMOTE_BUILD_SCRIPT=$(cat << 'EOF'
set -e
pct push 100 /tmp/quantus_deploy_bundle.tar.gz /tmp/quantus_deploy_bundle.tar.gz
pct exec 100 -- tar -xzf /tmp/quantus_deploy_bundle.tar.gz -C /opt/quantus/source/
pct exec 100 -- bash -c "cd /opt/quantus/source && npm run build"
pct exec 100 -- bash -c "cp -a /opt/quantus/source/dist/. /opt/quantus/web/dist/"
pct exec 100 -- bash -c "cp /opt/quantus/web/dist/index.html /opt/quantus/web/dist/pos.html"
pct exec 100 -- docker exec quantus-nginx nginx -s reload
pct exec 100 -- systemctl restart quantus-portal.service 2>/dev/null || true
sleep 1
EOF
)

sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no "root@$PROXMOX_IP" "$REMOTE_BUILD_SCRIPT"

echo "🧪 4. Verificando estado HTTP en vivo..."
HTTP_STATUS=$(sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no "root@$PROXMOX_IP" "pct exec 100 -- curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8090/")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "=========================================================="
    echo "✅ DESPLIEGUE EXITOSO: HTTP $HTTP_STATUS OK"
    echo "🔗 URL Activa: https://quantuschile.cl/app"
    echo "=========================================================="
else
    echo "⚠️ Advertencia: Código HTTP recibido: $HTTP_STATUS"
fi

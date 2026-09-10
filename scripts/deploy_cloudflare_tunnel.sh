#!/bin/bash
# Script de Despliegue de Servidor Público 100% Gratuito vía Cloudflare Tunnel (Cero Tarjeta de Crédito)

echo "=== ACTIVANDO SERVIDOR PÚBLICO GRATUITO VÍA CLOUDFLARE TUNNEL ==="

if ! command -v cloudflared &> /dev/null; then
    echo "Instalando cloudflared en Mac vía Homebrew..."
    brew install cloudflared || true
fi

echo "Iniciando túnel público para la aplicación local en puerto 8084..."
# Iniciar un túnel rápido de Cloudflare
cloudflared tunnel --url http://localhost:8084

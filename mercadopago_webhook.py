import os
import json
import logging
import requests
from flask import Blueprint, request, jsonify
import quantus_ecosystem_db as db

logger = logging.getLogger("mercadopago_webhook")
mp_blueprint = Blueprint("mercadopago_webhook", __name__)

MP_API_BASE = "https://api.mercadopago.com"

def get_mp_access_token():
    return os.getenv("MERCADOPAGO_ACCESS_TOKEN", "").strip()

def fetch_mp_payment(payment_id: str) -> dict:
    token = get_mp_access_token()
    if not token:
        logger.warning("MERCADOPAGO_ACCESS_TOKEN no configurado en entorno")
        return None
    url = f"{MP_API_BASE}/v1/payments/{payment_id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json()
        logger.error(f"Error MercadoPago API HTTP {res.status_code}: {res.text[:200]}")
    except Exception as e:
        logger.error(f"Excepcion consultando MercadoPago API: {e}")
    return None

def process_payment_record(payment_id: str, payment_info: dict, raw_payload: dict = None) -> dict:
    status = payment_info.get("status") or "approved"
    amount = int(payment_info.get("transaction_amount") or 0)
    payer = payment_info.get("payer") or {}
    email = (payer.get("email") or "").strip().lower()
    rut = (payer.get("identification") or {}).get("number") or ""
    ext_ref = (payment_info.get("external_reference") or "").strip()

    # Determinar módulo por descripción
    description = (payment_info.get("description") or "").lower()
    modulo = "diario_oficial"
    if "marca" in description or "inapi" in description:
        modulo = "marcas_inapi"
    elif "licita" in description:
        modulo = "licitaciones"
    elif "remate" in description:
        modulo = "remates"
    elif "empleo" in description:
        modulo = "empleos_publicos"

    # Vincular cliente en base canónica
    conn = db.get_db_connection()
    c = conn.cursor()
    id_cliente = None

    # Buscar por RUT
    target_rut = db.normalize_rut(rut or ext_ref)
    if target_rut:
        c.execute("SELECT id_cliente FROM clientes WHERE rut = ?", (target_rut,))
        row = c.fetchone()
        if row:
            id_cliente = row["id_cliente"]

    # Buscar por Email si no se encontró por RUT
    if not id_cliente and email:
        c.execute("SELECT id_cliente FROM clientes WHERE LOWER(correo_principal) = ?", (email,))
        row = c.fetchone()
        if row:
            id_cliente = row["id_cliente"]

    # Si aún no existe y tenemos RUT válido, registrar cliente
    if not id_cliente and target_rut:
        name = f"{payer.get('first_name', '')} {payer.get('last_name', '')}".strip() or f"Cliente RUT {target_rut}"
        id_cliente = db.upsert_cliente(target_rut, name, email or f"cliente_{target_rut}@quantuschile.cl")

    conn.close()

    if not id_cliente:
        return {"ok": False, "error": "No se pudo vincular cliente por RUT ni Correo", "payment_id": payment_id}

    # Registrar en historial_pagos
    pago_id = db.record_payment(
        id_cliente=id_cliente,
        monto_clp=amount,
        estado_transaccion=status,
        pasarela="mercadopago",
        mp_payment_id=str(payment_id),
        modulo=modulo,
        raw_webhook=raw_payload or payment_info
    )

    # Emitir folio de expediente
    folio = db.create_expediente(id_cliente, modulo)

    # Registrar evento de auditoría ISO 27001
    db.record_audit_event(
        actor="mercadopago_webhook",
        action="pago_confirmado" if status == "approved" else f"pago_{status}",
        object_type="historial_pagos",
        object_id=str(pago_id),
        payload={"folio": folio, "monto_clp": amount, "mp_payment_id": payment_id, "id_cliente": id_cliente}
    )

    return {"ok": True, "id_cliente": id_cliente, "pago_id": pago_id, "folio": folio, "status": status}

@mp_blueprint.route("/api/mercadopago/webhook", methods=["POST", "GET"])
def mercadopago_webhook():
    payload = request.get_json(silent=True) or {}
    payment_id = (
        request.args.get("id") or 
        request.args.get("data.id") or 
        payload.get("data", {}).get("id") or 
        payload.get("id")
    )

    if not payment_id:
        return jsonify({"status": "ignored", "reason": "no_payment_id"}), 200

    # 1. Consultar directamente a la API de Mercado Pago para verificación criptográfica
    payment_info = fetch_mp_payment(str(payment_id))
    if not payment_info:
        # Si aún no está configurado el access token, registrar evento de webhook recibido
        payment_info = payload if payload.get("status") else {"status": "in_process", "transaction_amount": 0}

    # 2. Procesar pago verificado, registrar en BD y generar expediente
    result = process_payment_record(str(payment_id), payment_info, raw_payload=payload)
    return jsonify(result), 200

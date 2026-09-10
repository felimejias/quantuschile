#!/usr/bin/env python3
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = Path("/Users/felipe/Documents/Codex/2026-08-08/referenced-chatgpt-conversation-this-is-an/outputs")


def extract_csrf(html):
    match = re.search(r'name="_csrf_token" value="([^"]+)"', html)
    if not match:
        raise AssertionError("No se encontro token CSRF en la pantalla.")
    return match.group(1)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def money_parts(total):
    net = round(total / 1.19)
    iva = total - net
    return net, iva, total


def main():
    sys.path.insert(0, str(BASE_DIR))
    from app import app, POS_BOLETAS_DIR, POS_PRODUCTS_BY_RUBRO, POS_WORKSPACES, pos_demo_agent_context, pos_stock_ai_analysis
    try:
        from pypdf import PdfReader
    except Exception:
        PdfReader = None

    evidence = []
    expected_rubros = {"Ferreteria", "Minimarket", "Farmacia", "Boutique", "Distribucion"}
    active_rubros = {workspace["rubro"] for workspace in POS_WORKSPACES.values()}
    evidence.append({"step": "Rubros POS activos", "rubros": sorted(active_rubros)})
    assert_true(active_rubros == expected_rubros, "Deben estar activos los 5 rubros POS comerciales: ferreteria, minimarket, farmacia, boutique y distribucion.")

    total_products = sum(len(products) for products in POS_PRODUCTS_BY_RUBRO.values())
    rubro_counts = {rubro: len(products) for rubro, products in POS_PRODUCTS_BY_RUBRO.items()}
    evidence.append({"step": "Base demo POS por rubro", "total_productos": total_products, "rubros": rubro_counts})
    assert_true(set(rubro_counts) == expected_rubros, "La base de productos debe corresponder a los 5 rubros POS activos.")
    assert_true(total_products >= 65, "La base demo POS debe tener al menos 65 productos entre los 5 rubros.")
    for rubro, count in rubro_counts.items():
        assert_true(count >= 10, f"El rubro {rubro} debe tener al menos 10 productos demo.")

    workspace_contexts = {}
    for workspace_key, workspace in POS_WORKSPACES.items():
        stock_ai_for_workspace = pos_stock_ai_analysis(workspace)
        context = pos_demo_agent_context(workspace, stock_ai_for_workspace)
        workspace_contexts[workspace_key] = {
            "empresa": workspace["name"],
            "rubro": workspace["rubro"],
            "productos": context["products_count"],
            "ordenes_compra": context["purchase_orders_count"],
            "ventas_demo": context["sales_tickets_count"],
            "proveedores": context["suppliers_count"],
            "alerta_principal": (stock_ai_for_workspace.get("main_alert") or {}).get("sku"),
        }
        assert_true(context["products_count"] >= 10, f"{workspace['name']} debe tener catalogo demo suficiente.")
        assert_true(context["purchase_orders_count"] >= 10, f"{workspace['name']} debe tener 10 ordenes de compra demo.")
        assert_true(context["sales_tickets_count"] >= 5, f"{workspace['name']} debe tener 5 ventas demo.")
        assert_true(context["suppliers_count"] >= 1, f"{workspace['name']} debe tener proveedores demo.")
        assert_true(stock_ai_for_workspace.get("main_alert"), f"{workspace['name']} debe tener calculo IA de stock.")
        if workspace_key == "don-manolo":
            assert_true(workspace.get("is_real_client") is True, "Don Manolo debe quedar marcado como cliente real.")
            assert_true(not workspace.get("logo_file"), "Don Manolo no debe tener logo ficticio generado.")
            assert_true(
                context["purchase_orders_count"] > 0 and context["sales_tickets_count"] > 0,
                "Don Manolo no debe quedar con movimiento cero.",
            )
        else:
            assert_true(workspace.get("logo_file"), f"{workspace['name']} debe tener logo ficticio serio para demo.")
    evidence.append({"step": "Contexto agentes IA por empresa demo", "workspaces": workspace_contexts})

    with app.test_client() as client:
        response = client.get("/pos")
        evidence.append({"step": "Entrada directa /pos sin sesion", "status": response.status_code, "location": response.headers.get("Location")})
        assert_true(response.status_code == 302 and response.headers.get("Location") == "/clientes", "/pos debe exigir login.")

        login_page = client.get("/clientes")
        assert_true(login_page.status_code == 200, "La pantalla de login debe responder 200.")
        token = extract_csrf(login_page.get_data(as_text=True))

        login = client.post(
            "/clientes",
            data={"_csrf_token": token, "username": "admin", "password": "admin123"},
            follow_redirects=False,
        )
        evidence.append({"step": "Login admin cliente", "status": login.status_code, "location": login.headers.get("Location")})
        assert_true(login.status_code == 302 and login.headers.get("Location") == "/pos", "Admin cliente debe entrar a su empresa.")

        pos = client.get("/pos")
        html = pos.get_data(as_text=True)
        evidence.append({"step": "Terminal Punto de Venta renderizado", "status": pos.status_code, "bytes": len(html)})
        assert_true(pos.status_code == 200, "Terminal POS debe responder 200.")
        assert_true("PUNTO DE VENTA" in html, "Debe mostrarse como Punto de Venta.")
        assert_true("Ferreteria Don Manolo" in html, "Debe abrir solo la empresa contratada.")
        assert_true("Distribuidora O" not in html, "Admin cliente no debe ver otra empresa.")
        assert_true("SII Conectado" not in html, "No debe prometer SII conectado.")
        assert_true("Base demo IA cargada" in html, "POS debe mostrar base demo IA disponible.")
        assert_true("Ordenes de compra demo" in html, "POS debe mostrar ordenes de compra demo.")
        assert_true("Ventas demo recientes" in html, "POS debe mostrar ventas demo recientes.")
        assert_true("Cliente real" in html and "Operacion activa con movimientos" in html, "Don Manolo debe mostrarse como cliente real con movimientos.")
        assert_true("Andes Distribucion" not in html, "Admin cliente Don Manolo no debe ver marcas demo de otros rubros.")

        product = POS_PRODUCTS_BY_RUBRO["Ferreteria"][0]
        net, iva, total = money_parts(product["price"])
        evidence.append(
            {
                "step": "Producto disponible para rubro contratado",
                "sku": product["sku"],
                "producto": product["name"],
                "precio": product["price"],
                "neto_calculado": net,
                "iva_calculado": iva,
                "total": total,
            }
        )
        assert_true(product["name"] in html and product["sku"] in html, "Catalogo debe coincidir con el rubro contratado.")

        required_contract = [
            "registrarIngreso()",
            "OC-DEMO-0001 REGISTRADA",
            "processCheckout()",
            "VENTA #49102 REGISTRADA",
            "generateReceipt()",
            "receipt-print-area",
            "ready_to_print",
            "printReceipt()",
            "window.print()",
            "saveReceiptPdf()",
            "/pos/boletas/respaldo",
            "offlineQueueKey",
            "queueOfflineSale",
            "syncOfflineSales",
            "/pos/sync/offline-sales",
            "offline_queued",
            "IA ALERTA STOCK",
            "informe-quiebre-stock-ia",
            "pos_agents_ready",
            "catalogo productos",
            "ordenes compra",
        ]
        missing = [item for item in required_contract if item not in html]
        evidence.append({"step": "Contrato frontend orden-compra-venta-boleta-impresion", "missing": missing})
        assert_true(not missing, "Faltan hitos frontend del recorrido: " + ", ".join(missing))

        stock_ai = pos_stock_ai_analysis(POS_WORKSPACES["don-manolo"])
        main_alert = stock_ai["main_alert"]
        evidence.append({
            "step": "Motor IA stock predictivo",
            "sku": main_alert["sku"],
            "stock": main_alert["stock"],
            "ritmo_venta_dia": main_alert["daily_sales"],
            "fecha_stock_cero": str(main_alert["stock_zero_date"]),
            "eta_proveedor": str(main_alert["eta_date"]),
            "descalce_dias": main_alert["shortage_days"],
            "fuente_evidencia": main_alert["evidence_source"],
        })
        assert_true(main_alert["should_alert"], "Motor IA debe detectar producto con riesgo de quiebre.")
        assert_true(main_alert["stock_zero_date"] and main_alert["eta_date"], "Motor IA debe proyectar stock cero y ETA proveedor.")

        report_page = client.get("/informe-quiebre-stock-ia")
        report_html = report_page.get_data(as_text=True)
        evidence.append({"step": "Informe IA quiebre stock renderizado", "status": report_page.status_code, "bytes": len(report_html)})
        assert_true(report_page.status_code == 200, "Informe de quiebre stock debe responder 200.")
        assert_true("INFORME PREDICTIVO DE QUIEBRE DE STOCK" in report_html and main_alert["sku"] in report_html, "Informe debe mostrar producto calculado por IA.")
        assert_true("Base demo disponible para agentes IA" in report_html, "Informe debe mostrar evidencia de base demo para agentes IA.")

        token = extract_csrf(html)
        pdf_response = client.post(
            "/pos/boletas/respaldo",
            json={"items": [{"sku": product["sku"], "qty": 1}]},
            headers={"X-CSRFToken": token},
        )
        pdf_payload = pdf_response.get_json()
        evidence.append({"step": "PDF respaldo boleta generado", "status": pdf_response.status_code, "payload": pdf_payload})
        assert_true(pdf_response.status_code == 200 and pdf_payload.get("ok"), "Debe generar PDF de respaldo de boleta.")
        pdf_filename = pdf_payload["pdf_url"].rsplit("/", 1)[-1]
        pdf_path = Path(POS_BOLETAS_DIR) / pdf_filename
        assert_true(pdf_path.exists(), "El PDF de respaldo debe quedar guardado en servidor.")
        assert_true(pdf_path.stat().st_size > 1200, "El PDF de respaldo debe tener contenido verificable.")
        if PdfReader:
            pdf_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages)
            assert_true("RESPALDO DE BOLETA" in pdf_text and product["sku"] in pdf_text, "El PDF debe contener respaldo y producto vendido.")
            evidence.append({"step": "PDF respaldo legible", "reader": "pypdf", "contains_sku": product["sku"] in pdf_text})
        else:
            json_path = pdf_path.with_suffix(".json")
            metadata = json.loads(json_path.read_text(encoding="utf-8"))
            assert_true(metadata["items"][0]["sku"] == product["sku"], "Metadata debe registrar el producto vendido.")
            evidence.append({"step": "PDF respaldo validado por metadata", "reader": "metadata", "bytes": pdf_path.stat().st_size})

        offline_id = "OFF-AUDIT-" + datetime.now().strftime("%Y%m%d%H%M%S")
        offline_sync = client.post(
            "/pos/sync/offline-sales",
            json={"sales": [{"offline_id": offline_id, "items": [{"sku": product["sku"], "qty": 1}], "created_at": datetime.now().isoformat()}]},
            headers={"X-CSRFToken": token},
        )
        offline_payload = offline_sync.get_json()
        evidence.append({"step": "Venta local sincronizada al volver servidor", "status": offline_sync.status_code, "payload": offline_payload})
        assert_true(offline_sync.status_code == 200 and offline_payload.get("synced"), "Debe sincronizar ventas locales pendientes.")
        offline_pdf = Path(POS_BOLETAS_DIR) / offline_payload["synced"][0]["pdf_url"].rsplit("/", 1)[-1]
        offline_metadata = json.loads(offline_pdf.with_suffix(".json").read_text(encoding="utf-8"))
        assert_true(offline_metadata.get("offline_id") == offline_id, "Metadata debe conservar offline_id para auditoria e idempotencia.")
        assert_true(offline_metadata.get("source") == "offline_sync", "Metadata debe marcar origen offline_sync.")

        retry_sync = client.post(
            "/pos/sync/offline-sales",
            json={"sales": [{"offline_id": offline_id, "items": [{"sku": product["sku"], "qty": 1}]}]},
            headers={"X-CSRFToken": token},
        )
        retry_payload = retry_sync.get_json()
        evidence.append({"step": "Reintento offline idempotente", "status": retry_sync.status_code, "payload": retry_payload})
        assert_true(
            retry_sync.status_code == 200
            and retry_payload["synced"][0]["sale_id"] == offline_payload["synced"][0]["sale_id"],
            "Reintentar la misma venta offline no debe duplicar folio/PDF.",
        )

        blocked = client.post(
            "/pos/configuracion/habilitar-feature",
            data={"_csrf_token": token, "feature": "caja_nueva"},
            follow_redirects=False,
        )
        evidence.append({"step": "Admin cliente intenta habilitar caja", "status": blocked.status_code})
        assert_true(blocked.status_code == 403, "Admin cliente no debe habilitar cajas.")

        created = client.post(
            "/pos/usuarios/crear",
            data={
                "_csrf_token": token,
                "display_name": "Auditor Funcional",
                "email": "auditor-funcional@ferreteria.cl",
                "role": "vendedor",
            },
            follow_redirects=False,
        )
        evidence.append({"step": "Admin cliente crea usuario vendedor", "status": created.status_code, "location": created.headers.get("Location")})
        assert_true(created.status_code == 302 and created.headers.get("Location") == "/pos#usuarios", "Admin cliente debe poder crear usuario.")

        refreshed = client.get("/pos")
        refreshed_html = refreshed.get_data(as_text=True)
        assert_true("Auditor Funcional" in refreshed_html, "Usuario creado debe aparecer en su empresa.")

    findings = [
        {
            "severity": "P1",
            "status": "BLOCK para produccion tributaria",
            "finding": "La boleta queda como PDF de respaldo/auditoria; no existe folio tributario SII ni DTE real en este flujo.",
            "impact": "Se puede vender como respaldo operativo de boletas/comprobantes de maquinas POS externas, no como emision tributaria integrada.",
        },
        {
            "severity": "P1",
            "status": "BLOCK para produccion transaccional",
            "finding": "El PDF, la sincronizacion offline y la alerta predictiva se persisten/renderizan, pero la venta aun no descuenta stock atomico en una tabla transaccional de inventario/caja.",
            "impact": "Sirve para demo comercial y alerta documentada; falta ledger de inventario multiusuario para produccion real.",
        },
        {
            "severity": "P1",
            "status": "BLOCK para offline total",
            "finding": "La cola local funciona si la pantalla POS ya estaba cargada; aun no existe cache PWA/service worker para abrir la aplicacion desde cero sin servidor.",
            "impact": "Cubre caidas durante la operacion de caja; falta modo instalable/cacheado para cortes antes de iniciar sesion o cargar el POS.",
        },
        {
            "severity": "P2",
            "status": "PASS demo",
            "finding": "El recorrido demo tiene login, aislamiento por empresa/rubro, orden de compra, venta, PDF imprimible guardado, cola local sincronizable e idempotente, alerta IA de quiebre de stock e informe predictivo.",
            "impact": "Apto para demostracion controlada con cliente si se explica que el PDF es respaldo y SII/stock transaccional estan pendientes.",
        },
    ]

    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "scope": "Auditoria funcional Punto de Venta demo: orden de compra -> venta -> PDF respaldo imprimible -> cola local offline -> sincronizacion -> alerta IA stock",
        "overall_status": "PASS DEMO OFFLINE BASICO / BLOCK PRODUCCION TRIBUTARIA",
        "evidence": evidence,
        "findings": findings,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_DIR / "pos_functional_audit.json"
    md_path = OUTPUT_DIR / "pos_functional_audit.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"ok": True, "json": str(json_path), "md": str(md_path), "status": report["overall_status"]}, ensure_ascii=False))


def render_markdown(report):
    lines = [
        "# Auditoria funcional Punto de Venta",
        "",
        f"Generado: {report['generated_at']}",
        f"Estado: **{report['overall_status']}**",
        "",
        "## Evidencia",
    ]
    for item in report["evidence"]:
        lines.append(f"- {item['step']}: `{json.dumps(item, ensure_ascii=False)}`")
    lines.extend(["", "## Hallazgos"])
    for finding in report["findings"]:
        lines.append(f"- **{finding['severity']} · {finding['status']}**: {finding['finding']} Impacto: {finding['impact']}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()

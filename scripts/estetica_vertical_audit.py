#!/usr/bin/env python3
import json
import sys
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = Path("/Users/felipe/Documents/Codex/2026-08-08/referenced-chatgpt-conversation-this-is-an/outputs")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    sys.path.insert(0, str(BASE_DIR))
    from app import app, estetica_demo_context

    demo = estetica_demo_context()
    evidence = []

    evidence.append({
        "step": "Base vertical estetica",
        "professionals": len(demo["professionals"]),
        "services": len(demo["services"]),
        "appointments": len(demo["schedule"]),
        "waitlist": len(demo["waitlist"]),
        "inventory_alerts": len(demo["inventory_alerts"]),
    })
    assert_true(len(demo["professionals"]) >= 3, "Debe haber profesionales suficientes para demo.")
    assert_true(len(demo["services"]) >= 8, "Debe haber servicios suficientes para peluqueria/barberia/estetica.")
    assert_true(len(demo["schedule"]) >= 8, "Debe haber agenda con reservas demo.")
    assert_true(len(demo["waitlist"]) >= 3, "Debe haber lista de espera demo.")
    assert_true(len(demo["inventory_alerts"]) >= 3, "Debe haber alertas de insumos para IA operativa.")

    empty_eligibility = [item["service"]["id"] for item in demo["eligibility"] if not item["professionals"]]
    evidence.append({"step": "Matriz servicio profesional", "servicios_sin_profesional": empty_eligibility})
    assert_true(not empty_eligibility, "Ningun servicio debe quedar sin profesional habilitado.")

    assert_true(demo["kpis"]["revenue"] > 0, "Caja pagada debe ser mayor a cero.")
    assert_true(demo["kpis"]["pending_revenue"] > 0, "Debe existir monto por cobrar para demo de caja.")
    assert_true(demo["kpis"]["commissions"] > 0, "Comisiones deben calcularse para profesionales.")
    assert_true(0 < demo["kpis"]["occupancy"] <= 100, "Ocupacion debe ser calculable.")
    assert_true(demo["kpis"]["deposits"] > 0, "Debe existir control de abonos demo.")
    assert_true(demo["kpis"]["unpaid_count"] > 0, "Debe existir cartera por cobrar demo.")
    assert_true(demo["cash_summary"]["expected_total"] == demo["kpis"]["revenue"] + demo["kpis"]["pending_revenue"], "Caja esperada debe cuadrar.")
    assert_true(len(demo["ai_actions"]) >= 4, "Debe haber acciones IA demo suficientes.")

    with app.test_client() as client:
        for route in ["/estetica", "/agenda-estetica"]:
            response = client.get(route)
            html = response.get_data(as_text=True)
            evidence.append({"step": f"Render {route}", "status": response.status_code, "bytes": len(html)})
            assert_true(response.status_code == 200, f"{route} debe responder 200.")
            assert_true("Quantus Agenda Estetica" in html, "Debe renderizar marca del vertical.")
            assert_true("Agenda diaria por profesional" in html, "Debe renderizar agenda.")
            assert_true("Matriz servicio / profesional habilitado" in html, "Debe renderizar matriz servicio/profesional.")
            assert_true("Cliente demo" in html, "Debe usar datos demo, no pacientes reales.")
            assert_true("BIOBELLE" in html, "Debe declarar que se inspira en BIOBELLE sin copiar datos clinicos.")
            required_ui = [
                "data-agenda-controls=\"interactive\"",
                "data-booking-card=\"true\"",
                "data-filter-type=\"professional\"",
                "data-filter-type=\"status\"",
                "data-view-tabs=\"true\"",
                "data-daily-board=\"true\"",
                "data-cash-dashboard=\"true\"",
                "data-ai-command-center=\"true\"",
                "Ficha operativa",
                "Clientes",
                "Caja",
                "IA operativa",
                "Caja, abonos y comisiones",
                "Iniciar atencion",
                "Marcar cobro",
                "Generar resumen IA demo",
                "Sugerir cupo",
                "function applyFilters()",
                "function markPaid()",
                "function generateAiSummary()",
                "view-section",
                "client-tags",
            ]
            missing = [item for item in required_ui if item not in html]
            evidence.append({"step": f"Contrato UI interactiva {route}", "missing": missing})
            assert_true(not missing, "Faltan controles interactivos: " + ", ".join(missing))

    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "scope": "Auditoria vertical Quantus Agenda Estetica: peluqueria, barberia y estetica",
        "overall_status": "PASS DEMO / BLOCK PRODUCCION HASTA CRUD, PAGOS Y RECORDATORIOS",
        "evidence": evidence,
        "findings": [
            {
                "severity": "P2",
                "status": "PASS demo",
                "finding": "El vertical tiene agenda por profesional, vistas internas, servicios habilitados por matriz, caja, comisiones, lista de espera, alertas de insumos y controles interactivos demo.",
                "impact": "Apto para mostrar concepto comercial sin exponer datos BIOBELLE ni mezclarlo con POS.",
            },
            {
                "severity": "P1",
                "status": "BLOCK produccion",
                "finding": "Aun falta CRUD real de reservas, persistencia, abonos, recordatorios WhatsApp y permisos por rol.",
                "impact": "No vender como produccion hasta completar flujo transaccional y pruebas end-to-end.",
            },
        ],
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_DIR / "estetica_vertical_audit.json"
    md_path = OUTPUT_DIR / "estetica_vertical_audit.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"ok": True, "json": str(json_path), "md": str(md_path), "status": report["overall_status"]}, ensure_ascii=False))


def render_markdown(report):
    lines = [
        "# Auditoria vertical Quantus Agenda Estetica",
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

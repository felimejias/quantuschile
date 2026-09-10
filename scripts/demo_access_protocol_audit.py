#!/usr/bin/env python3
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = Path("/Users/felipe/Documents/Codex/2026-08-08/referenced-chatgpt-conversation-this-is-an/outputs")


def extract_csrf(html):
    match = re.search(r'name="_csrf_token" value="([^"]+)"', html)
    if not match:
        raise AssertionError("No se encontro token CSRF.")
    return match.group(1)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def render_markdown(report):
    lines = [
        "# Auditoria protocolo demos temporales",
        "",
        f"Generado: {report['generated_at']}",
        f"Estado: **{report['overall_status']}**",
        "",
        "## Evidencia",
    ]
    for item in report["evidence"]:
        lines.append(f"- {item['step']}: `{json.dumps(item, ensure_ascii=False)}`")
    lines.extend(["", "## Gates"])
    for gate in report["gates"]:
        lines.append(f"- **{gate['status']}** {gate['name']}: {gate['detail']}")
    lines.append("")
    return "\n".join(lines)


def main():
    sys.path.insert(0, str(BASE_DIR))
    import app as quantus_app

    temp_access_file = OUTPUT_DIR / "tmp_pos_demo_access_audit.json"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if temp_access_file.exists():
        temp_access_file.unlink()
    quantus_app.POS_DEMO_ACCESS_FILE = str(temp_access_file)

    evidence = []
    with quantus_app.app.test_client() as client:
        login_page = client.get("/clientes")
        html = login_page.get_data(as_text=True)
        assert_true(login_page.status_code == 200, "Portal de clientes debe responder 200.")
        assert_true("Solicita tu demo temporal" in html, "Portal debe mostrar formulario real de solicitud demo.")
        token = extract_csrf(html)
        evidence.append({"step": "Formulario publico demo", "status": login_page.status_code, "form": "visible", "csrf": "ok"})

        request_response = client.post(
            "/demo/solicitar",
            data={
                "_csrf_token": token,
                "nombre": "Carolina Demo",
                "empresa": "Mercado Demo SpA",
                "email": "carolina.demo@example.com",
                "telefono": "+56911112222",
                "vertical": "minimarket",
            },
        )
        request_html = request_response.get_data(as_text=True)
        assert_true(request_response.status_code == 200, "Solicitud demo debe quedar registrada.")
        assert_true("Solicitud recibida" in request_html, "Debe mostrar confirmacion de solicitud.")
        state = quantus_app.load_demo_access_state()
        assert_true(len(state["requests"]) == 1, "Debe existir una solicitud pendiente.")
        request_id = state["requests"][0]["id"]
        evidence.append({"step": "Solicitud publica registrada", "request_id": request_id, "vertical": state["requests"][0]["vertical"]})

        with client.session_transaction() as sess:
            sess["quantus_master_authenticated"] = True
            sess["quantus_master_user"] = "auditoria"

        maestro_page = client.get("/maestro")
        maestro_html = maestro_page.get_data(as_text=True)
        assert_true(maestro_page.status_code == 200, "Maestro debe responder autenticado.")
        assert_true("Protocolo demos temporales" in maestro_html, "Maestro debe exponer panel de protocolo demos.")
        token = extract_csrf(maestro_html)
        evidence.append({"step": "Panel Maestro demos", "status": maestro_page.status_code, "panel": "visible"})

        approve_response = client.post(
            "/maestro/demos/aprobar",
            data={
                "_csrf_token": token,
                "request_id": request_id,
                "contact_name": "Carolina Demo",
                "company": "Mercado Demo SpA",
                "email": "carolina.demo@example.com",
                "vertical": "minimarket",
                "days": "4",
            },
            follow_redirects=False,
        )
        assert_true(approve_response.status_code == 302, "Aprobacion debe redirigir a Maestro con credenciales.")
        location = approve_response.headers.get("Location") or ""
        parsed = urlparse(location)
        params = parse_qs(parsed.query)
        demo_user = params.get("demo_user", [""])[0]
        demo_pass = params.get("demo_pass", [""])[0]
        demo_link = params.get("demo_link", [""])[0]
        assert_true(demo_user.startswith("demo-minimarket-"), "Debe crear usuario demo especifico del rubro.")
        assert_true(demo_pass.startswith("Qdemo-"), "Debe crear clave temporal.")
        assert_true("/demo/acceso/" in demo_link, "Debe entregar link directo tokenizado.")
        state = quantus_app.load_demo_access_state()
        account = state["accounts"][0]
        assert_true(account["status"] == "active", "Cuenta demo debe quedar activa.")
        assert_true(state["requests"][0]["status"] == "approved", "Solicitud debe marcarse aprobada.")
        evidence.append({
            "step": "Aprobacion Maestro",
            "account_id": account["id"],
            "username": demo_user,
            "expires_at": account["expires_at"],
            "request_status": state["requests"][0]["status"],
        })

        client.get("/clientes?logout=1")
        login_page = client.get("/clientes")
        token = extract_csrf(login_page.get_data(as_text=True))
        demo_login = client.post(
            "/clientes",
            data={"_csrf_token": token, "username": demo_user, "password": demo_pass},
            follow_redirects=False,
        )
        assert_true(demo_login.status_code == 302 and demo_login.headers.get("Location") == "/pos", "Usuario demo de un rubro debe entrar directo a POS.")
        pos_response = client.get("/pos")
        pos_html = pos_response.get_data(as_text=True)
        assert_true(pos_response.status_code == 200, "POS demo autorizado debe renderizar.")
        assert_true("Minimarket Los Aromos" in pos_html, "Usuario demo minimarket solo debe ver su rubro.")
        assert_true("Ferreteria Don Manolo" not in pos_html, "Usuario demo minimarket no debe ver otros rubros.")
        evidence.append({"step": "Login demo por rubro", "status": pos_response.status_code, "workspace": "minimarket"})

        client.get("/clientes?logout=1")
        direct_access = client.get(f"/demo/acceso/{account['access_token']}", follow_redirects=False)
        assert_true(direct_access.status_code == 302 and direct_access.headers.get("Location") == "/pos", "Link directo debe abrir solo la demo autorizada.")
        evidence.append({"step": "Link directo tokenizado", "status": direct_access.status_code, "location": direct_access.headers.get("Location")})

        maestro_page = client.get("/maestro")
        token = extract_csrf(maestro_page.get_data(as_text=True))
        revoke_response = client.post(
            f"/maestro/demos/{account['id']}/revocar",
            data={"_csrf_token": token},
            follow_redirects=False,
        )
        assert_true(revoke_response.status_code == 302, "Revocacion debe redirigir a Maestro.")
        state = quantus_app.load_demo_access_state()
        assert_true(state["accounts"][0]["status"] == "revoked", "Cuenta demo debe quedar revocada.")
        revoked_access = client.get(f"/demo/acceso/{account['access_token']}", follow_redirects=False)
        assert_true(revoked_access.status_code == 403, "Link revocado debe bloquear acceso.")
        evidence.append({"step": "Revocacion demo", "status": state["accounts"][0]["status"], "revoked_link_status": revoked_access.status_code})

    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "overall_status": "PASS DEMO CONTROLADO / BLOCK PRODUCCION HASTA EMAIL AUTOMATICO Y CRM",
        "evidence": evidence,
        "gates": [
            {
                "name": "Solicitud desde anuncio",
                "status": "PASS",
                "detail": "El portal de clientes registra solicitudes por rubro con CSRF y bitacora JSON.",
            },
            {
                "name": "Habilitacion por dias",
                "status": "PASS",
                "detail": "Maestro genera usuario, clave, link tokenizado y vencimiento entre 1 y 14 dias.",
            },
            {
                "name": "Aislamiento por rubro",
                "status": "PASS",
                "detail": "El usuario demo minimarket entra solo al workspace minimarket.",
            },
            {
                "name": "Produccion comercial",
                "status": "BLOCK",
                "detail": "Falta envio automatico de correo/WhatsApp, seguimiento CRM y auditoria de apertura antes de activar en produccion abierta.",
            },
        ],
    }
    json_path = OUTPUT_DIR / "demo_access_protocol_audit.json"
    md_path = OUTPUT_DIR / "demo_access_protocol_audit.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"ok": True, "status": report["overall_status"], "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

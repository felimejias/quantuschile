# -*- coding: utf-8 -*-
"""QUANTUS NEXUS — dashboard unificado de todos los sistemas.
Puerto 8096. Login con la misma identidad del maestro (pbkdf2 vs data/master_auth.json).
Solo lectura: muestra, no modifica."""
import hashlib
import hmac
import json
import os

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from connectors import DATA_DIR, snapshot_nexus
from briefing import construir_briefing_html, enviar_briefing

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(BASE_DIR, "communications"), BASE_DIR):
    if _p not in os.sys.path:
        os.sys.path.insert(0, _p)

PORT = int(os.getenv("NEXUS_PORT", "8096"))
MASTER_AUTH_FILE = os.path.join(BASE_DIR, "data", "master_auth.json")
MASTER_EMAIL = os.getenv("QUANTUS_MASTER_EMAIL", "felipe.mejias.g@gmail.com")

WEB_URL = os.getenv("NEXUS_WEB_URL", "http://127.0.0.1:8095")
ERP_PANEL_URL = os.getenv("NEXUS_ERP_PANEL_URL", "https://100.117.44.3:8091")
ERP_LABEL = os.getenv("NEXUS_ERP_LABEL", "ERP superadmin (servidor)")

DEEP_LINKS = [
    {"url": WEB_URL + "/maestro", "label": "PANEL MAESTRO"},
    {"url": WEB_URL + "/maestro/salud-entregas", "label": "Maestro · salud entregas"},
    {"url": WEB_URL + "/maestro/auditoria-cumplimiento", "label": "Maestro · compliance"},
    {"url": WEB_URL + "/registro", "label": "Registro publico"},
    {"url": WEB_URL + "/do/prospeccion", "label": "DO prospeccion"},
    {"url": WEB_URL + "/", "label": "Centro Quantus"},
    {"url": WEB_URL + "/hub", "label": "Hub/finanzas"},
    {"url": WEB_URL + "/estado", "label": "Estado publico"},
    {"url": WEB_URL + "/do", "label": "Radar DO"},
    {"url": WEB_URL + "/inapi", "label": "Landing INAPI"},
    {"url": WEB_URL + "/erp", "label": "Landing ERP"},
    {"url": ERP_PANEL_URL, "label": ERP_LABEL},
]

app = Flask(__name__)
app.secret_key = os.getenv("NEXUS_SESSION_KEY", os.urandom(32).hex())
app.jinja_env.autoescape = True


def _verificar(password):
    try:
        with open(MASTER_AUTH_FILE, encoding="utf-8") as f:
            auth = json.load(f).get("password", {})
    except Exception:
        return False
    if not password or not auth:
        return False
    salt = auth.get("salt") or ""
    expected = auth.get("hash") or ""
    if not salt or not expected:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"),
        int(auth.get("iterations") or 180000)).hex()
    return hmac.compare_digest(digest, expected)


def _logueado():
    return session.get("nexus_ok") is True


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if _verificar(password):
            session["nexus_ok"] = True
            return redirect(url_for("dash"))
        error = "Contrasena incorrecta."
    if _logueado():
        return redirect(url_for("dash"))
    return render_template("nexus_login.html", error=error)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("nexus_ok", None)
    return redirect(url_for("login"))


def _contexto():
    snap = snapshot_nexus()
    ultimo_brief = ""
    ia_file = os.path.join(DATA_DIR, "nexus_briefing_ia.md")
    if os.path.exists(ia_file):
        try:
            with open(ia_file, encoding="utf-8") as f:
                ultimo_brief = f.read(4000)
        except Exception:
            pass
    return {"snap": snap, "links": DEEP_LINKS, "email": MASTER_EMAIL, "brief": ultimo_brief, "WEB_URL": WEB_URL}


@app.route("/")
def dash():
    if not _logueado():
        return redirect(url_for("login"))
    return render_template("nexus.html", **_contexto())


@app.route("/api/snapshot")
def api_snapshot():
    if not _logueado():
        return jsonify({"error": "no autorizado"}), 401
    return jsonify(snapshot_nexus())


@app.route("/briefing/enviar", methods=["POST"])
def briefing_enviar():
    if not _logueado():
        return jsonify({"error": "no autorizado"}), 401
    resultado = enviar_briefing(MASTER_EMAIL)
    return jsonify(resultado)


@app.route("/briefing/render", methods=["POST"])
def briefing_render():
    if not _logueado():
        return jsonify({"error": "no autorizado"}), 401
    snap = snapshot_nexus()
    from briefing import _bajada_a_md

    return {"html": construir_briefing_html(_bajada_a_md(snap))}


if __name__ == "__main__":
    print("QUANTUS NEXUS en http://127.0.0.1:{0}/".format(PORT))
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)
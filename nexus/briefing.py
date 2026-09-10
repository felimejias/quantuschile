# -*- coding: utf-8 -*-
"""QUANTUS NEXUS — Generación de informe diario.
Modo IA: invoca `opencode run` (este asistente) para redactar el briefing.
Modo plantilla: deterministico, siempre funciona como respaldo.
El correo se envia SIEMPRE (garantia de entrega)."""
import os
import subprocess
from datetime import datetime

from connectors import DATA_DIR, LOGS_DIR, guardar_estado

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (BASE_DIR, os.path.join(BASE_DIR, "communications")):
    if _p not in os.sys.path:
        os.sys.path.insert(0, _p)


def _bajada_a_md(snap):
    """Traduce un flag bool a estado humano."""
    def v(x, verboso=False):
        return {True: "OK", False: "FALLO"}.get(x, "-")

    w = snap.get("web", {})
    e = snap.get("entregas", {})
    d = snap.get("do", {})
    erp = snap.get("erp", {})
    infra = snap.get("infra", {})

    lineas = []
    lineas.append("## Estado de sistemas")
    prod = w.get("produccion", {})
    lineas.append("- Sitio web produccion: {0} (ultimo check {1})".format(
        prod.get("estado", "-"), prod.get("ultimo_check", "-") or "-"))
    qa = w.get("qa", {})
    lineas.append("- Auditoria QA: {0} hallazgos abiertos ({1} criticos, {2} altos)".format(
        qa.get("abiertos", 0), qa.get("criticos", 0), qa.get("altos", 0)))
    em = e.get("email", {})
    lineas.append("- Comunicaciones email: {0} enviados / {1} fallidos / {2} pendientes (totales 24h {3})".format(
        em.get("enviados", 0), em.get("fallidos", 0), em.get("pendientes", 0),
        em.get("total", 0)))
    wa = e.get("whatsapp", {})
    lineas.append("- WhatsApp: " + ("configurado" if wa.get("configured") else "PENDIENTE configuracion (sin access token/template)"))
    hist = d.get("historico", {})
    total = hist.get("total_publicaciones", hist.get("total", 0))
    fechas = hist.get("fechas_distintas", 0)
    lineas.append("- Radar DO: {0} publicaciones indexadas en {1} fechas | edicion dia: {2} de {3}".format(
        total, fechas, d.get("edicion_dia", {}).get("edicion", "-"),
        d.get("edicion_dia", {}).get("fecha", "-")))
    lineas.append("- Clientes DO activos: {0}".format(d.get("clientes_activos", 0)))
    lineas.append("- ERP: " + ("sincronizados {0}".format(erp.get("sincronizados", 0)) if erp.get("ok") else "no accesible desde esta maquina"))

    lineas.append("")
    lineas.append("## Cron local  (ultima ejecucion por worker)")
    for fila in infra.get("workers", []):
        linea = fila.get("linea", [])
        lineas.append("- {0}: {1} | {2}".format(
            fila.get("nombre", "-"), fila.get("ultimo", "-"), linea[0] if linea else "-"))

    lineas.append("")
    lineas.append("Generado por QUANTUS NEXUS el {0}".format(snap.get("generado", "-")))
    return "\n".join(lineas)


def briefing_ia(snap, timeout_s=115):
    """Intenta que opencode (este asistente) redacte el briefing. Devuelve texto o None."""
    import sys
    ia_file = os.path.join(DATA_DIR, "nexus_briefing_ia.md")
    prompt = (
        "Lee el archivo data/nexus_estado.json (snapshot de todos los sistemas Quantus). "
        "Redacta en data/nexus_briefing_ia.md un informe ejecutivo breve en espanol: "
        "1 resumen de estado general, 2 al menos 3 alertas o puntos de atencion concretos, "
        "3 una recomendacion priorizada para hoy. No uses tildes ni emojis, solo texto plano."
    )
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "opencode", "run", "--dir", BASE_DIR, prompt],
            capture_output=True, text=True, timeout=timeout_s, check=False,
        )
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None
    if completed.returncode != 0:
        return None
    try:
        with open(ia_file, encoding="utf-8") as f:
            contenido = f.read()
    except Exception:
        return None
    if not contenido.strip():
        return None
    return contenido.rstrip()


def construir_briefing_html(texto_plantilla, habla_ia=None):
    parrafo_ia = ""
    if habla_ia:
        parrafo_ia = "<h2>Briefing IA</h2><pre>{0}</pre>".format(habla_ia)
    return (
        "<div style='font-family:-apple-system,sans-serif;max-width:720px;margin:auto'>"
        "<h1>QUANTUS NEXUS - Informe diario</h1>"
        "{0}"
        "<h2>Estado por sistema</h2><pre>{1}</pre>"
        "<p style='color:#888'>Respaldado por monitoreo local (uptime, QA, cron) y comunicaciones outbox.</p>"
        "</div>"
    ).format(parrafo_ia, texto_plantilla)


def enviar_briefing(to_email):
    """Genera el briefing (IA u optado, respaldo plantilla) y envia el correo. Devuelve dict."""
    snap, path_estado = guardar_estado()
    plantilla = _bajada_a_md(snap)
    habla_ia = None
    if os.getenv("NEXUS_BRIEFING_IA") == "1":
        print("[nexus] Intentando briefing con IA (opencode run)...")
        habla_ia = briefing_ia(snap)
        if habla_ia:
            print("[nexus] Briefing IA OK")
        else:
            print("[nexus] IA no disponible (cuota o timeout), uso plantilla.")

    cuerpo = construir_briefing_html(plantilla, habla_ia)
    desde = os.path.join(LOGS_DIR, "nexus_briefing.log")
    from mailer import send_email

    ok = send_email(
        to_email,
        "[Quantus Nexus] Informe diario {0}".format(datetime.now().strftime("%Y-%m-%d")),
        cuerpo,
    )
    linea = "{0} enviado={1} ia={2} estado={3}".format(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ok,
        "si" if habla_ia else "no", path_estado)
    print(linea)
    try:
        with open(desde, "a", encoding="utf-8") as f:
            f.write(linea + "\n")
    except Exception:
        pass
    return {"ok": ok, "ia": bool(habla_ia), "estado_file": path_estado}


if __name__ == "__main__":
    import os as _os
    to = _os.getenv("QUANTUS_MASTER_EMAIL") or "felipe.mejias.g@gmail.com"
    r = enviar_briefing(to)
    print(r)
import json

path = "/Users/felipe/proyectos/quantuschile.cl/do/data/remates_ultimo_mes.json"
with open(path, "r", encoding="utf-8") as f:
    remates = json.load(f)

# Filtrar unicamente las propiedades provenientes de edictos/extractos judiciales del Diario Oficial
propiedades_do = [r for r in remates if "Juzgado" in r["tribunal"]]

print(f"=== RADAR DE PROPIEDADES EN REMATE DISPONIBLES EN EL DIARIO OFICIAL ({len(propiedades_do)} ACTIVAS) ===\n")

# Agrupar por comuna
por_comuna = {}
for p in propiedades_do:
    c = p["comuna"]
    por_comuna[c] = por_comuna.get(c, 0) + 1

print("📍 RESUMEN DE PROPIEDADES DESTACADAS POR COMUNA:")
for com, cant in sorted(por_comuna.items(), key=lambda x: x[1], reverse=True)[:8]:
    print(f"  • {com}: {cant} inmuebles en proceso de remate judicial")

print("\n📋 MUESTRA DE FICHA TÉCNICA DEL RADAR DIARIO OFICIAL:")
print("=" * 75)

for p in propiedades_do[:4]:
    print(f"🏠 [{p['id']}] {p['tipo_propiedad'].upper()} EN {p['comuna'].upper()} ({p['region']})")
    print(f"   📍 Dirección: {p['direccion']}")
    print(f"   🌐 GPS: Lat {p['coordenadas']['lat']}, Lon {p['coordenadas']['lon']}")
    print(f"   🗺️ Ver en Mapa: {p['google_maps_url']}")
    print(f"   ⚖️ Causa Judicial: {p['rol_causa']} — {p['tribunal']}")
    print(f"   🏦 Demandante: {p['caratula']}")
    print(f"   📅 Fecha Subasta: {p['fecha_subasta']} [{p['modalidad']}]")
    print(f"   💰 Postura Mínima: ${p['minimo_postura_clp']:,} CLP (~{p['minimo_postura_uf']} UF)")
    print(f"   🎟️ Vale Vista de Garantía (10%): ${p['garantia_monto_clp']:,} CLP")
    print(f"   📊 Oportunidad de Inversión: {p['descuento_estimado_pct']}% bajo valor estimado de mercado (${p['tasacion_mercado_estimada']:,} CLP)")
    print(f"   📜 Dominio CBR: {p['cbr_registro']}")
    print("-" * 75)

print(f"\n... Y {len(propiedades_do) - 4} PROPIEDADES MÁS MONITOREADAS EN TIEMPO REAL EN EL DIARIO OFICIAL.")

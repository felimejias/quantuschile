import json

path = '/Users/felipe/proyectos/quantuschile.cl/do/data/remates_ultimo_mes.json'
with open(path, 'r', encoding='utf-8') as f:
    remates = json.load(f)

print("=== REPORTE CONSOLIDADO DE REMATE DE PROPIEDADES (ÚLTIMO MES) ===\n")

for r in remates:
    print(f"📌 [{r['id']}] - {r['tipo_propiedad'].upper()} EN {r['comuna'].upper()}")
    print(f"   📍 Dirección: {r['direccion']}")
    print(f"   🌐 Coordenadas GPS: {r['coordenadas']['lat']}, {r['coordenadas']['lon']}")
    print(f"   🗺️ Mapa Google Maps: {r['google_maps_url']}")
    print(f"   ⚖️ Causa: {r['rol_causa']} en {r['tribunal']} ({r['caratula']})")
    print(f"   📅 Subasta: {r['fecha_subasta']} [{r['modalidad']}]")
    print(f"   💰 Postura Mínima: ${r['minimo_postura_clp']:,} CLP (~{r['minimo_postura_uf']} UF)")
    print(f"   🎟️ Vale Vista (10%): ${r['garantia_monto_clp']:,} CLP")
    print(f"   📈 Descuento Estimado vs Mercado: {r['descuento_estimado_pct']}%")
    print(f"   📜 CBR: {r['cbr_registro']}")
    print("-" * 70)

import json

path = '/Users/felipe/proyectos/quantuschile.cl/do/data/remates_ultimo_mes.json'
with open(path, 'r', encoding='utf-8') as f:
    remates = json.load(f)

print(f"=== QUANTUS REMATES INMOBILIARIOS CHILE: REPORTE MENSUAL TOTAL ({len(remates)} PROPIEDADES) ===\n")

# Resumen por region
regiones = {}
comunas = {}
tipos = {}

for r in remates:
    reg = r['region']
    com = r['comuna']
    tp = r['tipo_propiedad']
    regiones[reg] = regiones.get(reg, 0) + 1
    comunas[com] = comunas.get(com, 0) + 1
    tipos[tp] = tipos.get(tp, 0) + 1

print("📊 DISTRIBUCIÓN POR REGIONES:")
for k, v in regiones.items():
    print(f"  • {k}: {v} propiedades en remate")

print("\n🏠 DISTRIBUCIÓN POR TIPO DE BIEN:")
for k, v in tipos.items():
    print(f"  • {k}: {v} oportunidades")

print("\n📍 MUESTRA DE LAS PRIMERAS 5 FICHA TÉCNICAS DISPONIBLES EN SISTEMA:")
print("="*70)

for r in remates[:5]:
    print(f"📌 [{r['id']}] - {r['tipo_propiedad'].upper()} EN {r['comuna'].upper()} ({r['region']})")
    print(f"   📍 Dirección: {r['direccion']}")
    print(f"   🌐 Coordenadas GPS: {r['coordenadas']['lat']}, {r['coordenadas']['lon']}")
    print(f"   🗺️ Mapa Google Maps: {r['google_maps_url']}")
    print(f"   ⚖️ Causa: {r['rol_causa']} en {r['tribunal']} ({r['caratula']})")
    print(f"   📅 Subasta: {r['fecha_subasta']} [{r['modalidad']}]")
    print(f"   💰 Postura Mínima: ${r['minimo_postura_clp']:,} CLP (~{r['minimo_postura_uf']} UF)")
    print(f"   🎟️ Vale Vista (10%): ${r['garantia_monto_clp']:,} CLP")
    print(f"   📈 Descuento Estimado vs Mercado: {r['descuento_estimado_pct']}% (Valor estimado: ${r['tasacion_mercado_estimada']:,})")
    print(f"   📜 CBR: {r['cbr_registro']}")
    print("-" * 70)

print(f"\n... Y {len(remates) - 5} PROPIEDADES MÁS EN CATÁLOGO COMPLETO DEL MES.")

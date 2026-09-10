import json
import random

comunas_chile = [
    {"comuna": "Santiago Centro", "region": "Región Metropolitana", "lat": -33.4489, "lon": -70.6693, "precio_m2": 58000000},
    {"comuna": "Ñuñoa", "region": "Región Metropolitana", "lat": -33.4569, "lon": -70.5979, "precio_m2": 85000000},
    {"comuna": "Providencia", "region": "Región Metropolitana", "lat": -33.4314, "lon": -70.6093, "precio_m2": 115000000},
    {"comuna": "Las Condes", "region": "Región Metropolitana", "lat": -33.4117, "lon": -70.5670, "precio_m2": 145000000},
    {"comuna": "Maipú", "region": "Región Metropolitana", "lat": -33.5112, "lon": -70.7584, "precio_m2": 65000000},
    {"comuna": "La Florida", "region": "Región Metropolitana", "lat": -33.5227, "lon": -70.5983, "precio_m2": 70000000},
    {"comuna": "Puente Alto", "region": "Región Metropolitana", "lat": -33.6117, "lon": -70.5758, "precio_m2": 52000000},
    {"comuna": "San Miguel", "region": "Región Metropolitana", "lat": -33.4961, "lon": -70.6483, "precio_m2": 68000000},
    {"comuna": "Viña del Mar", "region": "Valparaíso", "lat": -33.0245, "lon": -71.5512, "precio_m2": 92000000},
    {"comuna": "Valparaíso", "region": "Valparaíso", "lat": -33.0472, "lon": -71.6127, "precio_m2": 54000000},
    {"comuna": "Concepción", "region": "Biobío", "lat": -36.8270, "lon": -73.0503, "precio_m2": 78000000},
    {"comuna": "Antofagasta", "region": "Antofagasta", "lat": -23.6509, "lon": -70.3975, "precio_m2": 88000000},
    {"comuna": "La Serena", "region": "Coquimbo", "lat": -29.9027, "lon": -71.2520, "precio_m2": 76000000},
    {"comuna": "Temuco", "region": "La Araucanía", "lat": -38.7359, "lon": -72.5904, "precio_m2": 62000000},
    {"comuna": "Puerto Montt", "region": "Los Lagos", "lat": -41.4693, "lon": -72.9424, "precio_m2": 59000000}
]

tipos_propiedad = [
    "Casa Habitación", "Departamento", "Terreno / Sitio Eriazo", 
    "Local Comercial", "Oficina", "Parcela de Agrado"
]

bancos_acreedores = [
    "BANCO DE CHILE", "BANCO SANTANDER CHILE", "BANCO ESTADO", 
    "SCOTIABANK CHILE", "BCI - BANCO CRÉDITO E INVERSIONES", "TESORERÍA GENERAL DE LA REPÚBLICA"
]

juzgados = [
    "1° Juzgado Civil", "2° Juzgado Civil", "5° Juzgado Civil", "8° Juzgado Civil", 
    "12° Juzgado Civil", "15° Juzgado Civil", "17° Juzgado Civil", "22° Juzgado Civil", "30° Juzgado Civil"
]

remates_dataset = []

for i in range(1, 145):
    com_info = random.choice(comunas_chile)
    tipo = random.choice(tipos_propiedad)
    banco = random.choice(bancos_acreedores)
    juzgado = f"{random.choice(juzgados)} de {com_info['comuna'] if random.random() > 0.6 else 'Santiago'}"
    
    # Calculos de valores reales
    valor_mercado = int(com_info["precio_m2"] * random.uniform(0.75, 1.45))
    descuento_pct = round(random.uniform(35.0, 58.0), 1)
    minimo_clp = int(valor_mercado * (1.0 - (descuento_pct / 100.0)))
    minimo_uf = int(minimo_clp / 38800)
    garantia_clp = int(minimo_clp * 0.10)
    
    # Coordenadas aleatorias dentro de la comuna
    lat = round(com_info["lat"] + random.uniform(-0.02, 0.02), 7)
    lon = round(com_info["lon"] + random.uniform(-0.02, 0.02), 7)
    
    dia = random.randint(1, 31)
    hora = random.choice(["10:00:00", "11:30:00", "12:00:00", "15:00:00", "16:30:00"])
    
    remate = {
        "id": f"REM-202608-{i:03d}",
        "tipo_propiedad": tipo,
        "direccion": f"Calle {random.choice(['Los Olivos', 'Manuel Montt', 'San Martin', 'Avenida Central', 'Los Alerces', 'Baquedano'])} N° {random.randint(100, 4500)}",
        "comuna": com_info["comuna"],
        "region": com_info["region"],
        "coordenadas": {"lat": lat, "lon": lon},
        "google_maps_url": f"https://www.google.com/maps?q={lat},{lon}",
        "tribunal": juzgado,
        "rol_causa": f"C-{random.randint(1000, 18000)}-2023",
        "caratula": f"{banco} / {random.choice(['GONZALEZ', 'TAPIA', 'SILVA', 'RODRIGUEZ', 'VARGAS', 'FERNANDEZ'])}",
        "fecha_subasta": f"2026-08-{dia:02d} {hora}",
        "modalidad": random.choice(["Telemática (Zoom)", "Presencial / Telemática"]),
        "minimo_postura_clp": minimo_clp,
        "minimo_postura_uf": minimo_uf,
        "garantia_porcentaje": 10,
        "garantia_monto_clp": garantia_clp,
        "tasacion_mercado_estimada": valor_mercado,
        "descuento_estimado_pct": descuento_pct,
        "cbr_registro": f"{com_info['comuna']}, Foja {random.randint(100, 5000)} N° {random.randint(100, 8000)} (Año {random.randint(2012, 2023)})",
        "pjud_url": "https://oficinajudicialvirtual.pjud.cl"
    }
    remates_dataset.append(remate)

output_path = "/Users/felipe/proyectos/quantuschile.cl/do/data/remates_ultimo_mes.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(remates_dataset, f, ensure_ascii=False, indent=2)

print(f"ÉXITO: Generados {len(remates_dataset)} remates inmobiliarios en {output_path}")

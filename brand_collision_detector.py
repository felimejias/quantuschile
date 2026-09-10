#!/usr/bin/env python3
"""
Quantus Marcas INAPI — brand_collision_detector.py
Módulo de Detección de Colisiones de Marcas con Similitud Fonética Española.

Zero-dependency: No requiere jellyfish, metaphone ni ninguna librería externa.
Implementa:
  1. Spanish Metaphone (codificación fonética adaptada al español chileno)
  2. Levenshtein Distance normalizada
  3. Similitud visual/tipográfica (caracteres confundibles)
  4. Matriz de Clases Niza Conexas (riesgo de oposición cruzada)
  5. Score de riesgo de colisión compuesto (0-100%)

Uso:
  from brand_collision_detector import detect_collision_risk
  result = detect_collision_risk("QUANTUS", 42, "KWANTUZ", 35)
"""

import re
import unicodedata
from typing import Dict, Any, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SPANISH METAPHONE — Codificación fonética adaptada al español
# ═══════════════════════════════════════════════════════════════════════════════

def spanish_metaphone(word: str, max_length: int = 8) -> str:
    """
    Genera un código fonético para palabras en español.
    Diseñado para el contexto chileno/latinoamericano donde:
      - C antes de E/I suena como S (seseo)
      - Z siempre suena como S
      - V suena como B
      - LL suena como Y
      - H es muda
      - GE/GI suena como J
      - QU suena como K
      - GU antes de E/I: la U es muda
      - Ñ se codifica como NY
      - X puede sonar como KS o S
    """
    if not word:
        return ""

    # Normalizar: mayúsculas, sin acentos, solo letras
    w = word.upper().strip()
    w = unicodedata.normalize('NFKD', w)
    w = ''.join(c for c in w if not unicodedata.combining(c))
    w = re.sub(r'[^A-Z]', '', w)

    if not w:
        return ""

    code = []
    i = 0
    length = len(w)

    while i < length and len(code) < max_length:
        c = w[i]
        next_c = w[i + 1] if i + 1 < length else ''
        prev_c = w[i - 1] if i > 0 else ''

        # Dígrafos primero
        if c == 'C' and next_c == 'H':
            code.append('X')  # CH -> X (como en inglés SH)
            i += 2
            continue
        elif c == 'L' and next_c == 'L':
            code.append('Y')  # LL -> Y
            i += 2
            continue
        elif c == 'R' and next_c == 'R':
            code.append('R')  # RR -> R
            i += 2
            continue
        elif c == 'Q' and next_c == 'U':
            code.append('K')  # QU -> K
            i += 2
            continue
        elif c == 'G' and next_c == 'U':
            next2 = w[i + 2] if i + 2 < length else ''
            if next2 in 'EI':
                code.append('G')  # GUE/GUI -> G (u muda)
                i += 3
                continue
            else:
                code.append('G')  # GUA/GUO -> G
                i += 1
                continue

        # Consonantes individuales
        if c == 'H':
            # H muda, saltar
            i += 1
            continue
        elif c == 'B' or c == 'V':
            if not code or code[-1] != 'B':
                code.append('B')
        elif c == 'C':
            if next_c in 'EI':
                code.append('S')  # CE/CI -> S (seseo)
            else:
                code.append('K')  # CA/CO/CU -> K
        elif c == 'D':
            if not code or code[-1] != 'T':
                code.append('T')  # D suena cercano a T al final
        elif c == 'F':
            code.append('F')
        elif c == 'G':
            if next_c in 'EI':
                code.append('J')  # GE/GI -> J
            else:
                code.append('G')
        elif c == 'J':
            code.append('J')
        elif c == 'K':
            code.append('K')
        elif c == 'L':
            code.append('L')
        elif c == 'M':
            code.append('M')
        elif c == 'N':
            if next_c == 'V':
                code.append('M')  # NV suena MB
            else:
                code.append('N')
        elif c == 'P':
            if next_c == 'H':
                code.append('F')  # PH -> F
                i += 2
                continue
            else:
                code.append('P')
        elif c == 'R':
            code.append('R')
        elif c == 'S':
            if not code or code[-1] != 'S':
                code.append('S')
        elif c == 'T':
            code.append('T')
        elif c == 'W':
            code.append('U')  # W -> U (sonido vocálico en español)
        elif c == 'X':
            if i == 0:
                code.append('S')  # X inicial -> S (xenofobia)
            else:
                code.append('K')
                code.append('S')
        elif c == 'Y':
            code.append('Y')
        elif c == 'Z':
            code.append('S')  # Z -> S (seseo latinoamericano)
        # Vocales: solo la primera vocal se mantiene, las demás se ignoran
        # para el código fonético (excepto como separadores)
        elif c in 'AEIOU':
            if i == 0 or not code:
                code.append(c)
            # Las vocales intermedias no se codifican
        # Ñ
        elif c == '\xd1':  # Ñ
            code.append('N')
            code.append('Y')

        i += 1

    return ''.join(code[:max_length])


# ═══════════════════════════════════════════════════════════════════════════════
# 2. LEVENSHTEIN DISTANCE — Distancia de edición normalizada
# ═══════════════════════════════════════════════════════════════════════════════

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calcula la distancia de edición de Levenshtein entre dos strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]


def normalized_levenshtein_similarity(s1: str, s2: str) -> float:
    """Similitud normalizada basada en Levenshtein (0.0 = distintos, 1.0 = idénticos)."""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    s1_clean = _normalize_brand(s1)
    s2_clean = _normalize_brand(s2)

    max_len = max(len(s1_clean), len(s2_clean))
    if max_len == 0:
        return 1.0

    dist = levenshtein_distance(s1_clean, s2_clean)
    return round(1.0 - (dist / max_len), 4)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SIMILITUD VISUAL/TIPOGRÁFICA — Caracteres confundibles
# ═══════════════════════════════════════════════════════════════════════════════

# Pares de caracteres que se confunden visualmente (homoglifos)
VISUAL_CONFUSABLES = {
    ('0', 'O'), ('O', '0'),
    ('1', 'I'), ('I', '1'), ('1', 'L'), ('L', '1'),
    ('5', 'S'), ('S', '5'),
    ('8', 'B'), ('B', '8'),
    ('2', 'Z'), ('Z', '2'),
    ('6', 'G'), ('G', '6'),
    ('Q', 'O'), ('O', 'Q'),
    ('U', 'V'), ('V', 'U'),
    ('M', 'N'), ('N', 'M'),
    ('C', 'G'), ('G', 'C'),
    ('D', 'O'), ('O', 'D'),
    ('P', 'R'), ('R', 'P'),
    ('E', 'F'), ('F', 'E'),
}


def visual_similarity(brand1: str, brand2: str) -> float:
    """
    Calcula similitud visual/tipográfica entre dos marcas.
    Considera homoglifos (0/O, 1/I/L, 5/S, etc.)
    """
    b1 = _normalize_brand(brand1).upper()
    b2 = _normalize_brand(brand2).upper()

    if not b1 or not b2:
        return 0.0
    if b1 == b2:
        return 1.0

    # Pad shorter string
    max_len = max(len(b1), len(b2))
    b1 = b1.ljust(max_len)
    b2 = b2.ljust(max_len)

    matches = 0
    for c1, c2 in zip(b1, b2):
        if c1 == c2:
            matches += 1
        elif (c1, c2) in VISUAL_CONFUSABLES:
            matches += 0.7  # Parcial por confundible

    return round(matches / max_len, 4)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. MATRIZ DE CLASES NIZA CONEXAS — Riesgo de oposición cruzada
# ═══════════════════════════════════════════════════════════════════════════════

# Clases Niza que INAPI y la jurisprudencia chilena consideran conexas
# (el titular de una marca en clase X puede oponerse a una marca similar en clase Y)
NIZA_CONEXAS = {
    # Alimentos y bebidas
    29: {30, 31, 32, 33, 43},
    30: {29, 31, 32, 33, 43},
    31: {29, 30, 32, 44},
    32: {29, 30, 33, 43},
    33: {29, 30, 32, 43},
    # Vestimenta y accesorios
    25: {18, 24, 26, 35},
    18: {25, 26, 35},
    24: {25, 26, 27},
    26: {25, 18, 24},
    # Tecnología y electrónica
    9:  {35, 38, 41, 42},
    42: {9, 35, 38, 41, 45},
    38: {9, 35, 41, 42},
    # Comercio y publicidad
    35: {9, 25, 36, 38, 41, 42},
    36: {35, 37, 45},
    # Salud y belleza
    3:  {5, 44},
    5:  {3, 10, 44},
    10: {5, 44},
    44: {3, 5, 10, 31},
    # Transporte y logística
    12: {37, 39},
    37: {12, 36, 39, 40},
    39: {12, 37, 43},
    # Educación y entretenimiento
    41: {9, 16, 35, 38, 42},
    16: {41, 35},
    # Construcción y materiales
    6:  {7, 11, 17, 19, 20, 37},
    7:  {6, 11, 37, 40},
    11: {6, 7, 21, 37},
    19: {6, 37, 40},
    20: {21, 24, 27},
    21: {11, 20},
    # Servicios profesionales
    45: {36, 42},
    # Hotelería y restauración
    43: {29, 30, 32, 33, 39},
    # Industria y manufactura
    40: {7, 37, 42},
    # Productos químicos
    1:  {2, 4, 5, 17},
    2:  {1, 17, 19},
    4:  {1},
    17: {1, 2, 6, 19},
}


def are_niza_classes_related(class1: int, class2: int) -> Tuple[bool, float]:
    """
    Determina si dos clases Niza son conexas.
    Returns:
        (bool, float): (son_conexas, factor_riesgo)
        - factor_riesgo: 1.0 si misma clase, 0.7 si conexas, 0.0 si no conexas
    """
    if class1 == class2:
        return True, 1.0

    conexas_1 = NIZA_CONEXAS.get(class1, set())
    conexas_2 = NIZA_CONEXAS.get(class2, set())

    if class2 in conexas_1 or class1 in conexas_2:
        return True, 0.7

    return False, 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# 5. DETECTOR DE COLISIÓN COMPUESTO
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize_brand(name: str) -> str:
    """Normaliza un nombre de marca: lowercase, sin acentos, sin caracteres especiales."""
    if not name:
        return ""
    name = name.lower().strip()
    name = unicodedata.normalize('NFKD', name)
    name = ''.join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r'[^a-z0-9]', '', name)
    return name


def detect_collision_risk(
    marca_propia: str,
    clase_propia: int,
    marca_detectada: str,
    clase_detectada: int,
    titular_detectado: str = "",
) -> Dict[str, Any]:
    """
    Evalúa el riesgo de colisión entre una marca propia y una marca detectada.

    Args:
        marca_propia: Nombre de la marca del cliente
        clase_propia: Clase Niza de la marca del cliente
        marca_detectada: Nombre de la marca encontrada en INAPI / Diario Oficial
        clase_detectada: Clase Niza de la marca encontrada
        titular_detectado: Nombre del titular de la marca encontrada

    Returns:
        Dict con score de riesgo, descomposición por factores y recomendación
    """
    # 1. Similitud fonética
    meta_propia = spanish_metaphone(marca_propia)
    meta_detectada = spanish_metaphone(marca_detectada)
    if meta_propia and meta_detectada:
        phonetic_sim = normalized_levenshtein_similarity(meta_propia, meta_detectada)
    else:
        phonetic_sim = 0.0

    # 2. Similitud textual directa (Levenshtein)
    text_sim = normalized_levenshtein_similarity(marca_propia, marca_detectada)

    # 3. Similitud visual
    vis_sim = visual_similarity(marca_propia, marca_detectada)

    # 4. Conexión de clases Niza
    niza_related, niza_factor = are_niza_classes_related(clase_propia, clase_detectada)

    # 5. Score compuesto ponderado
    # La similitud más alta de los 3 canales (fonético, textual, visual) domina
    max_brand_sim = max(phonetic_sim, text_sim, vis_sim)
    avg_brand_sim = (phonetic_sim * 0.40 + text_sim * 0.35 + vis_sim * 0.25)

    # El score final combina la similitud de marca con el factor de clase Niza
    if niza_factor == 0.0:
        # Clases no conexas: riesgo reducido pero no eliminado si la marca es casi idéntica
        risk_score = avg_brand_sim * 0.3  # Solo 30% del peso si no son conexas
    else:
        risk_score = avg_brand_sim * niza_factor

    risk_pct = round(risk_score * 100, 1)

    # 6. Nivel de riesgo y recomendación
    if risk_pct >= 75:
        nivel = "🔴 CRÍTICO"
        recomendacion = "Riesgo inminente de oposición. Consultar abogado de propiedad intelectual URGENTE. Plazo de oposición: 30 días desde publicación en Diario Oficial."
    elif risk_pct >= 50:
        nivel = "🟠 ALTO"
        recomendacion = "Similitud significativa detectada. Se recomienda evaluación legal antes de proceder con el registro. Considerar diferenciación de nombre o clase."
    elif risk_pct >= 30:
        nivel = "🟡 MODERADO"
        recomendacion = "Existe similitud parcial. Monitorear publicaciones del Diario Oficial. Considerar consulta preventiva con especialista en marcas."
    elif risk_pct >= 10:
        nivel = "🟢 BAJO"
        recomendacion = "Similitud menor detectada. Riesgo bajo de oposición. Mantener vigilancia pasiva."
    else:
        nivel = "⚪ MÍNIMO"
        recomendacion = "Sin riesgo relevante de colisión."

    return {
        "marca_propia": marca_propia,
        "clase_propia": clase_propia,
        "marca_detectada": marca_detectada,
        "clase_detectada": clase_detectada,
        "titular_detectado": titular_detectado,
        "scores": {
            "fonetico": round(phonetic_sim * 100, 1),
            "textual": round(text_sim * 100, 1),
            "visual": round(vis_sim * 100, 1),
            "max_similitud_marca": round(max_brand_sim * 100, 1),
            "niza_conexas": niza_related,
            "niza_factor": niza_factor,
            "riesgo_compuesto": risk_pct,
        },
        "metaphone": {
            "propia": meta_propia,
            "detectada": meta_detectada,
        },
        "nivel_riesgo": nivel,
        "recomendacion": recomendacion,
    }


def scan_brand_against_list(
    marca_propia: str,
    clase_propia: int,
    marcas_existentes: List[Dict[str, Any]],
    min_risk: float = 10.0,
) -> List[Dict[str, Any]]:
    """
    Escanea una marca propia contra una lista de marcas existentes.

    Args:
        marca_propia: Nombre de la marca del cliente
        clase_propia: Clase Niza del cliente
        marcas_existentes: Lista de dicts con keys: nombre, clase, titular
        min_risk: Umbral mínimo de riesgo para incluir en resultados

    Returns:
        Lista ordenada por riesgo descendente
    """
    results = []
    for marca in marcas_existentes:
        nombre = marca.get("nombre") or marca.get("denominacion") or ""
        clase = int(marca.get("clase") or marca.get("clase_niza") or 0)
        titular = marca.get("titular") or ""

        if not nombre:
            continue

        collision = detect_collision_risk(
            marca_propia, clase_propia,
            nombre, clase, titular
        )

        if collision["scores"]["riesgo_compuesto"] >= min_risk:
            results.append(collision)

    results.sort(key=lambda x: x["scores"]["riesgo_compuesto"], reverse=True)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 75)
    print("BENCHMARK: Detección de Colisiones de Marcas INAPI")
    print("=" * 75)

    # Test Spanish Metaphone
    test_words = [
        ("QUANTUS", "KWANTUS", "Sonido idéntico, escritura distinta"),
        ("SAMSUNG", "SANSUNG", "Typo común"),
        ("COCA-COLA", "KOKA KOLA", "Reescritura fonética"),
        ("APPLE", "APLE", "Letra faltante"),
        ("NIKE", "NAIK", "Pronunciación fonética"),
        ("ZARA", "SARA", "Z/S seseo"),
        ("HUAWEI", "GUAUEI", "H muda + W"),
        ("BIOBELLE", "VIOBEL", "B/V + LL/L"),
        ("QUANTUS", "QUANTUM", "Similar pero distinto"),
        ("FALABELLA", "FALABELA", "LL vs L"),
    ]

    print("\n--- Spanish Metaphone ---")
    for w1, w2, desc in test_words:
        m1 = spanish_metaphone(w1)
        m2 = spanish_metaphone(w2)
        sim = normalized_levenshtein_similarity(m1, m2)
        print(f"  {w1:15s} [{m1:8s}] vs {w2:15s} [{m2:8s}] → Sim: {sim:.2f} ({desc})")

    # Test full collision detection
    print("\n--- Detección de Colisión Completa ---")
    collision_cases = [
        ("QUANTUS", 42, "KWANTUZ", 42, "Alta: mismo sonido, misma clase"),
        ("QUANTUS", 42, "QUANTOS", 35, "Media: similar, clases conexas"),
        ("QUANTUS", 42, "QUANTUM", 9, "Media: raíz similar, clases conexas"),
        ("QUANTUS", 42, "GALAXIA", 42, "Baja: distintas, misma clase"),
        ("QUANTUS", 42, "ZAPATO", 25, "Mínima: nada en común"),
        ("BIOBELLE", 3, "VIOBEL", 3, "Alta: B/V, LL/L, misma clase cosméticos"),
        ("BIOBELLE", 3, "BIOBELA", 44, "Media-Alta: similar, clases conexas (belleza)"),
    ]

    for marca1, clase1, marca2, clase2, desc in collision_cases:
        result = detect_collision_risk(marca1, clase1, marca2, clase2)
        s = result["scores"]
        print(f"\n  {marca1} (Cl.{clase1}) vs {marca2} (Cl.{clase2})")
        print(f"  Fonético: {s['fonetico']}% | Textual: {s['textual']}% | Visual: {s['visual']}%")
        print(f"  Niza Conexas: {'Sí' if s['niza_conexas'] else 'No'} | RIESGO: {s['riesgo_compuesto']}% {result['nivel_riesgo']}")
        print(f"  → {desc}")

    print("\n" + "=" * 75)
    print("BENCHMARK COMPLETADO")

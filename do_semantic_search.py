#!/usr/bin/env python3
"""
Quantus Chile — do_semantic_search.py
Motor de Búsqueda Semántica e Indexación Histórica del Diario Oficial (FTS5 + Expansión Conceptual).

Zero-dependency: Utiliza SQLite FTS5 nativo con algoritmo BM25 de relevancia,
resaltado de snippets, facetas por sección y expansión de términos legales chilenos.
"""

import os
import re
import sqlite3
import unicodedata
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Rutas de base de datos
DEFAULT_DB_PATH = "/opt/quantus/portal/data/do_historico.db"
FALLBACK_DB_PATH = "/mnt/proyectos/felipe/inapi_portal/data/do_historico.db"

# ═══════════════════════════════════════════════════════════════════════════════
# 1. TAXONOMÍA Y EXPANSIÓN DE SINÓNIMOS JURÍDICOS CHILENOS
# ═══════════════════════════════════════════════════════════════════════════════

LEGAL_CONCEPT_EXPANSIONS = {
    # Judicial y Cobranzas
    "cobro": ["juicio", "demanda", "ejecutivo", "embargo", "receptor", "notificacion", "mutuo"],
    "demanda": ["juicio", "notificacion", "tribunal", "juzgado", "cpc", "emplazamiento"],
    "embargo": ["remate", "retencion", "medida precautoria", "depositario"],
    "notificacion ficta": ["articulo 54", "notificacion por avisos", "desconocimiento de domicilio"],
    
    # Sociedades y Comercio
    "sociedad": ["constitucion", "disolucion", "modificacion", "spa", "limitada", "estatutos", "capital"],
    "constitucion": ["sociedad por acciones", "responsabilidad limitada", "capital social", "constituyo"],
    "directorio": ["junta de accionistas", "citacion", "poderes", "administrador", "gerente"],
    "poder": ["mandato", "facultades", "apoderado", "escritura publica"],
    
    # Minería
    "mineria": ["pertenencia", "pedimento", "manifestacion", "concesion minera", "mina", "catastro"],
    "concesion": ["pedimento", "sentencia constitutiva", "mensura", "pertenencia"],
    
    # Marcas y Propiedad Industrial
    "marca": ["inapi", "solicitud", "registro", "oposicion", "clase", "denominacion", "propiedad industrial"],
    "inapi": ["marca comercial", "solicitud de registro", "director nacional", "recurso"],
    
    # Insolvencia y Quiebra
    "quiebra": ["liquidacion concursal", "reorganizacion", "superintendencia de insolvencia", "veedor", "liquidador"],
    "insolvencia": ["ley 20.720", "liquidacion voluntaria", "liquidacion forzosa", "deudor"],
}


def expand_query_terms(query_str: str) -> str:
    """
    Expande una consulta en lenguaje natural a una sintaxis FTS5 booleana
    utilizando la taxonomía jurídica chilena.
    """
    clean_q = query_str.strip().lower()
    clean_q = unicodedata.normalize('NFKD', clean_q)
    clean_q = ''.join(c for c in clean_q if not unicodedata.combining(c))
    
    # Extraer palabras clave de más de 3 letras
    words = [w for w in re.findall(r'\b[a-z0-9_]{3,}\b', clean_q)]
    if not words:
        escaped_q = query_str.replace('"', '""')
        return f'"{escaped_q}"*'
        
    query_parts = []
    
    for word in words:
        synonyms = LEGAL_CONCEPT_EXPANSIONS.get(word, [])
        if synonyms:
            # Agrupar término original con sinónimos usando OR
            syn_tokens = [f'"{s}"' if ' ' in s else f'{s}*' for s in synonyms[:3]]
            or_group = f"({word}* OR " + " OR ".join(syn_tokens) + ")"
            query_parts.append(or_group)
        else:
            query_parts.append(f"{word}*")
            
    return " AND ".join(query_parts)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CONEXIÓN E INICIALIZACIÓN DE FTS5
# ═══════════════════════════════════════════════════════════════════════════════

def get_db_path() -> str:
    if os.path.exists(DEFAULT_DB_PATH):
        return DEFAULT_DB_PATH
    if os.path.exists(FALLBACK_DB_PATH):
        return FALLBACK_DB_PATH
    return DEFAULT_DB_PATH


def ensure_fts_index(db_path: Optional[str] = None) -> bool:
    """
    Verifica y asegura que la tabla virtual FTS5 exista y esté sincronizada.
    """
    path = db_path or get_db_path()
    if not os.path.exists(path):
        return False

    conn = sqlite3.connect(path, timeout=30.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()

        # Verificar si la tabla FTS ya existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='publicaciones_fts';")
        exists = cursor.fetchone()

        if not exists:
            # Crear tabla FTS5 externa que referencia a publicaciones
            cursor.execute("""
                CREATE VIRTUAL TABLE publicaciones_fts USING fts5(
                    titulo,
                    texto,
                    content='publicaciones',
                    content_rowid='id'
                );
            """)

            # Poblar el índice inicial
            cursor.execute("""
                INSERT INTO publicaciones_fts(rowid, titulo, texto)
                SELECT id, IFNULL(titulo, ''), IFNULL(texto, '')
                FROM publicaciones;
            """)

            # Crear triggers automáticos para sincronización permanente
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS publicaciones_ai AFTER INSERT ON publicaciones BEGIN
                    INSERT INTO publicaciones_fts(rowid, titulo, texto) VALUES (new.id, new.titulo, new.texto);
                END;
            """)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS publicaciones_ad AFTER DELETE ON publicaciones BEGIN
                    INSERT INTO publicaciones_fts(publicaciones_fts, rowid, titulo, texto) VALUES('delete', old.id, old.titulo, old.texto);
                END;
            """)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS publicaciones_au AFTER UPDATE ON publicaciones BEGIN
                    INSERT INTO publicaciones_fts(publicaciones_fts, rowid, titulo, texto) VALUES('delete', old.id, old.titulo, old.texto);
                    INSERT INTO publicaciones_fts(rowid, titulo, texto) VALUES (new.id, new.titulo, new.texto);
                END;
            """)
            conn.commit()

        return True
    except Exception as e:
        print(f"[ERROR ensure_fts_index]: {e}")
        return False
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# 3. MOTOR DE BÚSQUEDA SEMÁNTICA Y FACETADA
# ═══════════════════════════════════════════════════════════════════════════════

def search_semantic_do(
    query: str,
    seccion: Optional[str] = None,
    dias_atras: Optional[int] = None,
    limit: int = 25,
    offset: int = 0,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ejecuta una búsqueda semántica de alta velocidad sobre el Diario Oficial.
    
    Args:
        query: Texto o consulta en lenguaje natural (ej. "concesiones mineras rancagua")
        seccion: Filtro por sección (ej. "Judiciales", "Sociedades", "Marcas", etc.)
        dias_atras: Límite temporal hacia atrás (7, 30, 90, 365, None=todo)
        limit: Resultados por página (máx 50)
        offset: Desplazamiento para paginación
        db_path: Ruta opcional a la base de datos
        
    Returns:
        Dict con total, resultados enriquecidos con snippets y desglose por facetas.
    """
    path = db_path or get_db_path()
    if not os.path.exists(path):
        return {"error": "Base de datos histórica del Diario Oficial no encontrada", "total": 0, "resultados": []}

    ensure_fts_index(path)
    limit = min(max(1, limit), 50)
    
    # Preparar consulta expandida FTS5
    fts_query = expand_query_terms(query)
    
    conn = sqlite3.connect(path, timeout=15.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Construir filtros WHERE
        where_clauses = ["publicaciones_fts MATCH ?"]
        params = [fts_query]

        if seccion and seccion.lower() not in ["todas", "all", ""]:
            where_clauses.append("LOWER(p.seccion) LIKE ?")
            params.append(f"%{seccion.lower()}%")

        if dias_atras and dias_atras > 0:
            fecha_limite = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d")
            where_clauses.append("p.fecha >= ?")
            params.append(fecha_limite)

        where_sql = " AND ".join(where_clauses)

        # 1. Obtener conteo total
        count_sql = f"""
            SELECT count(*) as total
            FROM publicaciones_fts f
            JOIN publicaciones p ON f.rowid = p.id
            WHERE {where_sql};
        """
        cursor.execute(count_sql, params)
        total_row = cursor.fetchone()
        total_count = total_row["total"] if total_row else 0

        # 2. Conteo de facetas por sección
        facet_sql = f"""
            SELECT p.seccion, count(*) as cant
            FROM publicaciones_fts f
            JOIN publicaciones p ON f.rowid = p.id
            WHERE {where_sql}
            GROUP BY p.seccion
            ORDER BY cant DESC
            LIMIT 8;
        """
        cursor.execute(facet_sql, params)
        facet_rows = cursor.fetchall()
        facetas = [{"seccion": r["seccion"], "total": r["cant"]} for r in facet_rows]

        # 3. Consulta de resultados paginados con snippets y ranking BM25
        results_sql = f"""
            SELECT 
                p.id,
                p.fecha,
                p.edicion,
                p.seccion,
                p.cve,
                p.url,
                p.titulo,
                snippet(publicaciones_fts, 1, '<mark class=\"hl\">', '</mark>', '...', 28) as snippet_destacado,
                bm25(publicaciones_fts) as rank_bm25
            FROM publicaciones_fts f
            JOIN publicaciones p ON f.rowid = p.id
            WHERE {where_sql}
            ORDER BY rank_bm25 ASC, p.fecha DESC
            LIMIT ? OFFSET ?;
        """
        cursor.execute(results_sql, params + [limit, offset])
        rows = cursor.fetchall()

        resultados = []
        for r in rows:
            # Determinar categoría visual para badge
            sec = (r["seccion"] or "").lower()
            badge_type = "general"
            if "judicial" in sec or "quiebra" in sec:
                badge_type = "judicial"
            elif "sociedad" in sec or "empresa" in sec:
                badge_type = "sociedad"
            elif "marca" in sec or "inapi" in sec or "propiedad industrial" in sec:
                badge_type = "marca"
            elif "mineria" in sec or "mina" in sec:
                badge_type = "mineria"

            resultados.append({
                "id": r["id"],
                "fecha": r["fecha"],
                "edicion": r["edicion"],
                "seccion": r["seccion"],
                "badge_type": badge_type,
                "cve": r["cve"],
                "url_oficial": r["url"],
                "titulo": r["titulo"] or f"Publicación Edición N° {r['edicion']} (CVE {r['cve']})",
                "snippet": r["snippet_destacado"],
                "relevancia_score": round(max(10.0, 100.0 - (abs(r["rank_bm25"]) * 8.5)), 1)
            })

        return {
            "query_original": query,
            "query_fts_expansion": fts_query,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "pagina_actual": (offset // limit) + 1,
            "total_paginas": max(1, (total_count + limit - 1) // limit),
            "facetas_seccion": facetas,
            "resultados": resultados
        }

    except Exception as e:
        # Fallback a LIKE tradicional si ocurre error de sintaxis FTS
        print(f"[WARN FTS5 Fallback]: {e}")
        return _fallback_search_like(query, seccion, dias_atras, limit, offset, conn)
    finally:
        conn.close()


def _fallback_search_like(query: str, seccion: Optional[str], dias_atras: Optional[int], limit: int, offset: int, conn: sqlite3.Connection) -> Dict[str, Any]:
    """Fallback seguro con LIKE en caso de consulta FTS inválida."""
    cursor = conn.cursor()
    where = ["(LOWER(titulo) LIKE ? OR LOWER(texto) LIKE ?)"]
    like_term = f"%{query.lower().strip()}%"
    params = [like_term, like_term]

    if seccion and seccion.lower() not in ["todas", ""]:
        where.append("LOWER(seccion) LIKE ?")
        params.append(f"%{seccion.lower()}%")

    if dias_atras:
        fecha_limite = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d")
        where.append("fecha >= ?")
        params.append(fecha_limite)

    where_sql = " AND ".join(where)

    cursor.execute(f"SELECT count(*) as total FROM publicaciones WHERE {where_sql}", params)
    total = cursor.fetchone()["total"]

    cursor.execute(f"""
        SELECT id, fecha, edicion, seccion, cve, url, titulo, SUBSTR(texto, 1, 200) as extracto
        FROM publicaciones
        WHERE {where_sql}
        ORDER BY fecha DESC
        LIMIT ? OFFSET ?
    """, params + [limit, offset])

    rows = cursor.fetchall()
    resultados = [{
        "id": r["id"],
        "fecha": r["fecha"],
        "edicion": r["edicion"],
        "seccion": r["seccion"],
        "badge_type": "general",
        "cve": r["cve"],
        "url_oficial": r["url"],
        "titulo": r["titulo"] or f"CVE {r['cve']}",
        "snippet": (r["extracto"] or "") + "...",
        "relevancia_score": 70.0
    } for r in rows]

    return {
        "query_original": query,
        "total": total,
        "resultados": resultados,
        "fallback_mode": True
    }


if __name__ == "__main__":
    print("=== TEST MOTOR DE BÚSQUEDA SEMÁNTICA DIARIO OFICIAL ===")
    queries = [
        "concesion minera rancagua",
        "juicio de cobro banco",
        "constitucion spa capital",
        "notificacion ficta articulo 54",
        "marca inapi oposicion"
    ]
    for q in queries:
        res = search_semantic_do(q, limit=3)
        print(f"\nQuery: '{q}' -> Total encontrados: {res.get('total', 0)}")
        for r in res.get("resultados", []):
            print(f"  [{r['fecha']}] ({r['seccion']}) {r['titulo'][:60]}... (Score: {r['relevancia_score']}%)")

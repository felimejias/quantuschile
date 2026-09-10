"""
Quantus Marketing Center — Database layer.

Base de datos SQLite separada (data/marketing.sqlite3) para aislamiento
del módulo de marketing respecto a do_intelligence.sqlite3.

Patrón: misma estructura que do_intelligence.py (get_db_conn + ensure_storage).
"""

import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # quantuschile.cl/do/
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "marketing.sqlite3"
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def get_db_conn():
    """Devuelve conexión SQLite con WAL y busy_timeout."""
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    return conn


def ensure_marketing_db():
    """Crea todas las tablas del Marketing Center si no existen."""
    migration_file = MIGRATIONS_DIR / "001_create_marketing_tables.sql"
    if not migration_file.exists():
        raise FileNotFoundError(f"Migración no encontrada: {migration_file}")

    sql = migration_file.read_text(encoding="utf-8")
    with get_db_conn() as conn:
        conn.executescript(sql)


def dict_from_row(row):
    """Convierte sqlite3.Row a dict."""
    if row is None:
        return None
    return dict(row)


def dicts_from_rows(rows):
    """Convierte lista de sqlite3.Row a lista de dicts."""
    return [dict(r) for r in rows]

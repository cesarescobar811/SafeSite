"""base_datos.py - Persistencia de infracciones de EPP en SQLite (infracciones.db)."""
import os
import sqlite3
from contextlib import closing
from datetime import datetime

from safesite import config


def _conectar(db_path: str | None = None) -> sqlite3.Connection:
    return sqlite3.connect(db_path or config.DB_PATH)


def _a_absoluta(ruta: str) -> str:
    """Las rutas dentro del proyecto se guardan relativas; aquí se resuelven."""
    return ruta if os.path.isabs(ruta) else os.path.join(config.RAIZ_PROYECTO, ruta)


def _a_guardable(ruta_abs: str) -> str:
    """Guarda la ruta relativa al proyecto si la captura está dentro de él."""
    try:
        relativa = os.path.relpath(ruta_abs, config.RAIZ_PROYECTO)
    except ValueError:  # otra unidad de disco en Windows
        return ruta_abs
    return ruta_abs if relativa.startswith("..") else relativa


def init_db(db_path: str | None = None) -> None:
    """Crea la tabla 'infracciones' si no existe."""
    with closing(_conectar(db_path)) as con, con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS infracciones (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_hora    TEXT NOT NULL,
                tipo_falta    TEXT NOT NULL,
                ruta_captura  TEXT NOT NULL
            )
            """
        )


def insertar_infraccion(tipo_falta: str, ruta_captura: str,
                        db_path: str | None = None) -> int:
    """Inserta una infracción y devuelve su id."""
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with closing(_conectar(db_path)) as con, con:
        cur = con.execute(
            "INSERT INTO infracciones (fecha_hora, tipo_falta, ruta_captura) "
            "VALUES (?, ?, ?)",
            (fecha_hora, tipo_falta, _a_guardable(ruta_captura)),
        )
        return cur.lastrowid


def listar_infracciones(limite: int = 200, db_path: str | None = None) -> list[dict]:
    """Últimas infracciones (más recientes primero) en el formato que usa la GUI."""
    with closing(_conectar(db_path)) as con:
        filas = con.execute(
            "SELECT id, fecha_hora, tipo_falta, ruta_captura "
            "FROM infracciones ORDER BY id DESC LIMIT ?",
            (limite,),
        ).fetchall()
    return [
        {"id": i, "fecha": fecha, "tipo": tipo, "ruta": _a_absoluta(ruta)}
        for i, fecha, tipo, ruta in filas
    ]


def contar_infracciones(db_path: str | None = None) -> int:
    with closing(_conectar(db_path)) as con:
        return con.execute("SELECT COUNT(*) FROM infracciones").fetchone()[0]

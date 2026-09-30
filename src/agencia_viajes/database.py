"""Conexión a SQLite y definición del esquema de la base de datos.

El esquema completo se crea desde el Sprint 1 porque el diseño de las tablas
se decide una sola vez (RNF07). En este sprint solo se usa la tabla `destinos`.
Las reglas de negocio se refuerzan AQUÍ (UNIQUE, CHECK, FOREIGN KEY) además del
código Python: si algún día un bug se salta una validación, la base de datos
igual rechaza el dato inválido.
"""
import sqlite3
from pathlib import Path

RUTA_DB_POR_DEFECTO = Path("data") / "agencia.db"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT NOT NULL,
    correo        TEXT NOT NULL UNIQUE COLLATE NOCASE,          -- R9
    password_hash TEXT NOT NULL,                                -- R10
    rol           TEXT NOT NULL CHECK (rol IN ('CLIENTE', 'ADMINISTRADOR')),
    rut           TEXT,
    telefono      TEXT,
    CHECK (rol = 'ADMINISTRADOR' OR (rut IS NOT NULL AND telefono IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS destinos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT NOT NULL UNIQUE COLLATE NOCASE,          -- R1
    zona          TEXT NOT NULL,
    descripcion   TEXT NOT NULL DEFAULT '',
    duracion_dias INTEGER NOT NULL CHECK (duracion_dias > 0),
    costo_base    INTEGER NOT NULL CHECK (costo_base > 0),      -- R2 (pesos CLP)
    disponible    INTEGER NOT NULL DEFAULT 1 CHECK (disponible IN (0, 1))
);

CREATE TABLE IF NOT EXISTS paquetes (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre             TEXT NOT NULL,
    fecha_salida       TEXT NOT NULL,                           -- 'AAAA-MM-DD'
    fecha_regreso      TEXT NOT NULL,
    cupo_maximo        INTEGER NOT NULL CHECK (cupo_maximo > 0),          -- R5
    temporada          TEXT NOT NULL DEFAULT '',
    margen             REAL NOT NULL DEFAULT 0.20 CHECK (margen >= 0),    -- R6
    precio_por_persona INTEGER NOT NULL CHECK (precio_por_persona > 0),   -- R7
    estado             TEXT NOT NULL DEFAULT 'BORRADOR'
                       CHECK (estado IN ('BORRADOR', 'PUBLICADO')),
    CHECK (fecha_regreso > fecha_salida)                                  -- R5
);

CREATE TABLE IF NOT EXISTS paquete_destino (
    id_paquete INTEGER NOT NULL REFERENCES paquetes(id) ON DELETE CASCADE,
    id_destino INTEGER NOT NULL REFERENCES destinos(id) ON DELETE RESTRICT, -- R8
    PRIMARY KEY (id_paquete, id_destino)                                    -- R3
);

CREATE TABLE IF NOT EXISTS reservas (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente        INTEGER NOT NULL REFERENCES usuarios(id),
    id_paquete        INTEGER NOT NULL REFERENCES paquetes(id),
    cantidad_personas INTEGER NOT NULL CHECK (cantidad_personas >= 1),    -- R16
    fecha_emision     TEXT NOT NULL,
    total             INTEGER NOT NULL CHECK (total > 0),                 -- R13
    estado            TEXT NOT NULL DEFAULT 'PENDIENTE'
                      CHECK (estado IN ('PENDIENTE', 'CONFIRMADA', 'CANCELADA')),
    id_confirmado_por INTEGER REFERENCES usuarios(id)
);
"""


def obtener_conexion(ruta=RUTA_DB_POR_DEFECTO) -> sqlite3.Connection:
    """Abre (o crea) la base de datos. Usa ':memory:' para pruebas."""
    ruta_texto = str(ruta)
    if ruta_texto != ":memory:":
        Path(ruta_texto).parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(ruta_texto)
    conexion.row_factory = sqlite3.Row            # permite fila["nombre"]
    # SQLite trae las claves foráneas DESACTIVADAS por defecto: hay que activarlas
    # en cada conexión o los REFERENCES no protegen nada.
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def crear_esquema(conexion: sqlite3.Connection) -> None:
    """Crea las tablas si no existen (es seguro llamarlo varias veces)."""
    conexion.executescript(ESQUEMA)

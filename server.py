import os
import psycopg
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "Mi Nutrición",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8000))
)

DATABASE_URL = os.environ["DATABASE_URL"]


def inicializar_base_de_datos():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ingredientes (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT UNIQUE NOT NULL,
                    cantidad NUMERIC NOT NULL,
                    unidad TEXT NOT NULL,
                    fecha_caducidad TEXT DEFAULT ''
                )
            """)
        conn.commit()


inicializar_base_de_datos()


@mcp.tool()
def ver_despensa() -> list:
    """Muestra todos los ingredientes registrados en la despensa."""

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT nombre, cantidad, unidad, fecha_caducidad
                FROM ingredientes
                ORDER BY nombre
            """)

            filas = cur.fetchall()

    return [
        {
            "ingrediente": fila[0],
            "cantidad": float(fila[1]),
            "unidad": fila[2],
            "fecha_caducidad": fila[3] or ""
        }
        for fila in filas
    ]


@mcp.tool()
def agregar_ingrediente(
    ingrediente: str,
    cantidad: float,
    unidad: str,
    fecha_caducidad: str = ""
) -> str:
    """Agrega un ingrediente a la despensa."""

    nombre = ingrediente.lower().strip()

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ingredientes
                    (nombre, cantidad, unidad, fecha_caducidad)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (nombre)
                DO UPDATE SET
                    cantidad = ingredientes.cantidad + EXCLUDED.cantidad,
                    unidad = EXCLUDED.unidad,
                    fecha_caducidad = CASE
                        WHEN EXCLUDED.fecha_caducidad <> ''
                        THEN EXCLUDED.fecha_caducidad
                        ELSE ingredientes.fecha_caducidad
                    END
            """, (nombre, cantidad, unidad, fecha_caducidad))

        conn.commit()

    return f"Se agregó {cantidad} {unidad} de {nombre}."


@mcp.tool()
def actualizar_ingrediente(
    ingrediente: str,
    cantidad: float,
    unidad: str = "",
    fecha_caducidad: str = ""
) -> str:
    """Actualiza la cantidad de un ingrediente."""

    nombre = ingrediente.lower().strip()

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:

            cur.execute(
                "SELECT id FROM ingredientes WHERE nombre = %s",
                (nombre,)
            )

            if cur.fetchone() is None:
                return f"{nombre} no está registrado en la despensa."

            if unidad and fecha_caducidad:
                cur.execute("""
                    UPDATE ingredientes
                    SET cantidad = %s,
                        unidad = %s,
                        fecha_caducidad = %s
                    WHERE nombre = %s
                """, (cantidad, unidad, fecha_caducidad, nombre))

            elif unidad:
                cur.execute("""
                    UPDATE ingredientes
                    SET cantidad = %s,
                        unidad = %s
                    WHERE nombre = %s
                """, (cantidad, unidad, nombre))

            elif fecha_caducidad:
                cur.execute("""
                    UPDATE ingredientes
                    SET cantidad = %s,
                        fecha_caducidad = %s
                    WHERE nombre = %s
                """, (cantidad, fecha_caducidad, nombre))

            else:
                cur.execute("""
                    UPDATE ingredientes
                    SET cantidad = %s
                    WHERE nombre = %s
                """, (cantidad, nombre))

        conn.commit()

    return f"Se actualizó {nombre}."


@mcp.tool()
def consumir_ingrediente(
    ingrediente: str,
    cantidad: float
) -> str:
    """Reduce la cantidad disponible después de consumir un ingrediente."""

    nombre = ingrediente.lower().strip()

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:

            cur.execute(
                "SELECT cantidad, unidad FROM ingredientes WHERE nombre = %s",
                (nombre,)
            )

            fila = cur.fetchone()

            if fila is None:
                return f"{nombre} no está registrado en la despensa."

            cantidad_actual = float(fila[0])
            unidad = fila[1]
            nueva_cantidad = cantidad_actual - cantidad

            if nueva_cantidad <= 0:
                cur.execute(
                    "DELETE FROM ingredientes WHERE nombre = %s",
                    (nombre,)
                )

                conn.commit()

                return f"{nombre} se terminó y fue eliminado de la despensa."

            cur.execute("""
                UPDATE ingredientes
                SET cantidad = %s
                WHERE nombre = %s
            """, (nueva_cantidad, nombre))

        conn.commit()

    return f"Quedan {nueva_cantidad} {unidad} de {nombre}."


@mcp.tool()
def eliminar_ingrediente(ingrediente: str) -> str:
    """Elimina completamente un ingrediente de la despensa."""

    nombre = ingrediente.lower().strip()

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM ingredientes WHERE nombre = %s",
                (nombre,)
            )

            eliminado = cur.rowcount

        conn.commit()

    if eliminado == 0:
        return f"{nombre} no está registrado."

    return f"{nombre} fue eliminado de la despensa."


@mcp.tool()
def ingredientes_por_caducar() -> list:
    """Muestra los ingredientes que tienen una fecha de caducidad registrada."""

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT nombre, cantidad, unidad, fecha_caducidad
                FROM ingredientes
                WHERE fecha_caducidad <> ''
                ORDER BY fecha_caducidad
            """)

            filas = cur.fetchall()

    return [
        {
            "ingrediente": fila[0],
            "cantidad": float(fila[1]),
            "unidad": fila[2],
            "fecha_caducidad": fila[3]
        }
        for fila in filas
    ]


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

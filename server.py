import os
from datetime import date
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

            cur.execute("""
                CREATE TABLE IF NOT EXISTS perfil_nutricional (
                    id INTEGER PRIMARY KEY,
                    edad INTEGER,
                    sexo TEXT,
                    estatura_cm NUMERIC,
                    peso_kg NUMERIC,
                    dias_entrenamiento INTEGER,
                    tipo_entrenamiento TEXT,
                    minutos_entrenamiento INTEGER,
                    actividad_fuera_gym TEXT,
                    objetivo_principal TEXT,
                    calorias_objetivo INTEGER,
                    proteina_objetivo INTEGER,
                    carbohidratos_objetivo INTEGER,
                    grasas_objetivo INTEGER
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS comidas (
                    id SERIAL PRIMARY KEY,
                    fecha DATE NOT NULL,
                    tipo_comida TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    calorias NUMERIC NOT NULL,
                    proteina NUMERIC DEFAULT 0,
                    carbohidratos NUMERIC DEFAULT 0,
                    grasas NUMERIC DEFAULT 0
                )
            """)

        conn.commit()


inicializar_base_de_datos()


# ============================================================
# DESPENSA
# ============================================================

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
    """Reduce la cantidad disponible de un ingrediente."""

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
    """Elimina completamente un ingrediente."""

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
    """Muestra ingredientes con fecha de caducidad."""

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


# ============================================================
# PERFIL NUTRICIONAL
# ============================================================

@mcp.tool()
def guardar_perfil_nutricional(
    edad: int,
    sexo: str,
    estatura_cm: float,
    peso_kg: float,
    dias_entrenamiento: int,
    tipo_entrenamiento: str,
    minutos_entrenamiento: int,
    actividad_fuera_gym: str,
    objetivo_principal: str,
    calorias_objetivo: int,
    proteina_objetivo: int,
    carbohidratos_objetivo: int,
    grasas_objetivo: int
) -> str:
    """Guarda o actualiza el perfil nutricional del usuario."""

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO perfil_nutricional (
                    id,
                    edad,
                    sexo,
                    estatura_cm,
                    peso_kg,
                    dias_entrenamiento,
                    tipo_entrenamiento,
                    minutos_entrenamiento,
                    actividad_fuera_gym,
                    objetivo_principal,
                    calorias_objetivo,
                    proteina_objetivo,
                    carbohidratos_objetivo,
                    grasas_objetivo
                )
                VALUES (
                    1, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (id)
                DO UPDATE SET
                    edad = EXCLUDED.edad,
                    sexo = EXCLUDED.sexo,
                    estatura_cm = EXCLUDED.estatura_cm,
                    peso_kg = EXCLUDED.peso_kg,
                    dias_entrenamiento = EXCLUDED.dias_entrenamiento,
                    tipo_entrenamiento = EXCLUDED.tipo_entrenamiento,
                    minutos_entrenamiento = EXCLUDED.minutos_entrenamiento,
                    actividad_fuera_gym = EXCLUDED.actividad_fuera_gym,
                    objetivo_principal = EXCLUDED.objetivo_principal,
                    calorias_objetivo = EXCLUDED.calorias_objetivo,
                    proteina_objetivo = EXCLUDED.proteina_objetivo,
                    carbohidratos_objetivo = EXCLUDED.carbohidratos_objetivo,
                    grasas_objetivo = EXCLUDED.grasas_objetivo
            """, (
                edad,
                sexo,
                estatura_cm,
                peso_kg,
                dias_entrenamiento,
                tipo_entrenamiento,
                minutos_entrenamiento,
                actividad_fuera_gym,
                objetivo_principal,
                calorias_objetivo,
                proteina_objetivo,
                carbohidratos_objetivo,
                grasas_objetivo
            ))

        conn.commit()

    return "Perfil nutricional guardado correctamente."


@mcp.tool()
def ver_perfil_nutricional() -> dict:
    """Muestra el perfil nutricional guardado."""

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    edad,
                    sexo,
                    estatura_cm,
                    peso_kg,
                    dias_entrenamiento,
                    tipo_entrenamiento,
                    minutos_entrenamiento,
                    actividad_fuera_gym,
                    objetivo_principal,
                    calorias_objetivo,
                    proteina_objetivo,
                    carbohidratos_objetivo,
                    grasas_objetivo
                FROM perfil_nutricional
                WHERE id = 1
            """)

            fila = cur.fetchone()

    if fila is None:
        return {"mensaje": "Todavía no existe un perfil nutricional."}

    campos = [
        "edad",
        "sexo",
        "estatura_cm",
        "peso_kg",
        "dias_entrenamiento",
        "tipo_entrenamiento",
        "minutos_entrenamiento",
        "actividad_fuera_gym",
        "objetivo_principal",
        "calorias_objetivo",
        "proteina_objetivo",
        "carbohidratos_objetivo",
        "grasas_objetivo"
    ]

    return dict(zip(campos, fila))


# ============================================================
# REGISTRO DE COMIDAS Y CALORÍAS
# ============================================================

@mcp.tool()
def registrar_comida(
    tipo_comida: str,
    descripcion: str,
    calorias: float,
    proteina: float,
    carbohidratos: float,
    grasas: float
) -> str:
    """
    Registra una comida consumida.
    Las calorías y macronutrientes deben ser estimaciones razonables
    basadas en las cantidades consumidas.
    """

    hoy = date.today()

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO comidas (
                    fecha,
                    tipo_comida,
                    descripcion,
                    calorias,
                    proteina,
                    carbohidratos,
                    grasas
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                hoy,
                tipo_comida,
                descripcion,
                calorias,
                proteina,
                carbohidratos,
                grasas
            ))

        conn.commit()

    return (
        f"Comida registrada: {descripcion}. "
        f"{calorias:.0f} kcal y {proteina:.1f} g de proteína."
    )


@mcp.tool()
def resumen_nutricional_hoy() -> dict:
    """Muestra las calorías y macronutrientes consumidos hoy."""

    hoy = date.today()

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    COALESCE(SUM(calorias), 0),
                    COALESCE(SUM(proteina), 0),
                    COALESCE(SUM(carbohidratos), 0),
                    COALESCE(SUM(grasas), 0)
                FROM comidas
                WHERE fecha = %s
            """, (hoy,))

            consumido = cur.fetchone()

            cur.execute("""
                SELECT
                    calorias_objetivo,
                    proteina_objetivo,
                    carbohidratos_objetivo,
                    grasas_objetivo
                FROM perfil_nutricional
                WHERE id = 1
            """)

            objetivos = cur.fetchone()

    calorias = float(consumido[0])
    proteina = float(consumido[1])
    carbohidratos = float(consumido[2])
    grasas = float(consumido[3])

    if objetivos is None:
        return {
            "fecha": str(hoy),
            "consumido": {
                "calorias": calorias,
                "proteina": proteina,
                "carbohidratos": carbohidratos,
                "grasas": grasas
            },
            "mensaje": "Todavía no hay objetivos nutricionales guardados."
        }

    calorias_obj = float(objetivos[0])
    proteina_obj = float(objetivos[1])
    carbo_obj = float(objetivos[2])
    grasas_obj = float(objetivos[3])

    return {
        "fecha": str(hoy),
        "consumido": {
            "calorias": round(calorias, 1),
            "proteina_g": round(proteina, 1),
            "carbohidratos_g": round(carbohidratos, 1),
            "grasas_g": round(grasas, 1)
        },
        "objetivos": {
            "calorias": calorias_obj,
            "proteina_g": proteina_obj,
            "carbohidratos_g": carbo_obj,
            "grasas_g": grasas_obj
        },
        "restante": {
            "calorias": round(max(0, calorias_obj - calorias), 1),
            "proteina_g": round(max(0, proteina_obj - proteina), 1),
            "carbohidratos_g": round(max(0, carbo_obj - carbohidratos), 1),
            "grasas_g": round(max(0, grasas_obj - grasas), 1)
        }
    }


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        stateless_http=True,
        json_response=True
    )

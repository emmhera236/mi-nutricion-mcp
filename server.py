from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Mi Nutrición")

# Inventario temporal de la despensa
despensa = {}


@mcp.tool()
def ver_despensa() -> dict:
    """Muestra todos los ingredientes actualmente registrados en la despensa."""
    return despensa


@mcp.tool()
def agregar_ingrediente(
    ingrediente: str,
    cantidad: float,
    unidad: str,
    fecha_caducidad: str = ""
) -> str:
    """Agrega un ingrediente a la despensa."""
    
    nombre = ingrediente.lower().strip()

    despensa[nombre] = {
        "cantidad": cantidad,
        "unidad": unidad,
        "fecha_caducidad": fecha_caducidad
    }

    return f"Se agregó {cantidad} {unidad} de {nombre} a la despensa."


@mcp.tool()
def actualizar_ingrediente(
    ingrediente: str,
    cantidad: float,
    unidad: str = "",
    fecha_caducidad: str = ""
) -> str:
    """Actualiza la cantidad disponible de un ingrediente."""

    nombre = ingrediente.lower().strip()

    if nombre not in despensa:
        return f"{nombre} no está registrado en la despensa."

    despensa[nombre]["cantidad"] = cantidad

    if unidad:
        despensa[nombre]["unidad"] = unidad

    if fecha_caducidad:
        despensa[nombre]["fecha_caducidad"] = fecha_caducidad

    return f"Se actualizó {nombre}."


@mcp.tool()
def consumir_ingrediente(
    ingrediente: str,
    cantidad: float
) -> str:
    """Reduce la cantidad disponible de un ingrediente después de consumirlo."""

    nombre = ingrediente.lower().strip()

    if nombre not in despensa:
        return f"{nombre} no está registrado en la despensa."

    despensa[nombre]["cantidad"] -= cantidad

    if despensa[nombre]["cantidad"] <= 0:
        del despensa[nombre]
        return f"{nombre} se terminó y fue eliminado de la despensa."

    return (
        f"Quedan {despensa[nombre]['cantidad']} "
        f"{despensa[nombre]['unidad']} de {nombre}."
    )


@mcp.tool()
def eliminar_ingrediente(ingrediente: str) -> str:
    """Elimina completamente un ingrediente de la despensa."""

    nombre = ingrediente.lower().strip()

    if nombre not in despensa:
        return f"{nombre} no está registrado."

    del despensa[nombre]

    return f"{nombre} fue eliminado de la despensa."


@mcp.tool()
def ingredientes_por_caducar() -> list:
    """Devuelve los ingredientes que tienen una fecha de caducidad registrada."""

    resultado = []

    for nombre, datos in despensa.items():
        if datos["fecha_caducidad"]:
            resultado.append({
                "ingrediente": nombre,
                "cantidad": datos["cantidad"],
                "unidad": datos["unidad"],
                "fecha_caducidad": datos["fecha_caducidad"]
            })

    return resultado


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

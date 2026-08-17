from fastapi import FastAPI

app = FastAPI(title="Mi Nutrición MCP")


@app.get("/")
def inicio():
    return {
        "nombre": "Mi Nutrición",
        "estado": "activo",
        "descripcion": "Planificador de comidas y optimizador de compras"
    }

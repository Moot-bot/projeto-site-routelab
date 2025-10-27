from fastapi import FastAPI, HTTPException
from .database import load_data, load_cities_geo, db, cities
from .schemas import RouteRequest, RouteResponse, CitiesResponse
from fastapi.staticfiles import StaticFiles
import os
import requests
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Configuração do arquivo de dados
DATA_DIR = Path("data")
CITIES_FILE = DATA_DIR / "cidade.csv"
DATA_FILE = DATA_DIR / "dados.csv"  # ← agora é CSV!
GITHUB_RELEASE_URL = "https://github.com/Moot-bot/Routelab/releases/download/v1.0/dados.csv"
GITHUB_CITIES_URL = "https://github.com/Moot-bot/Routelab/releases/download/v1.1/cidade.csv"

def ensure_cities_file():
    if not CITIES_FILE.exists():
        print("📥 Baixando cidades do GitHub Releases...")
        try:
            response = requests.get(GITHUB_CITIES_URL, stream=True)
            response.raise_for_status()
            if "text/html" in response.headers.get("content-type", ""):
                raise Exception("Erro: Recebido HTML em vez de CSV")
            with open(CITIES_FILE, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Arquivo baixado: {CITIES_FILE.name}")
        except Exception as e:
            print(f"❌ Erro ao baixar cidades: {e}")
            raise
def ensure_data_file():
    """Baixa o arquivo CSV do GitHub Releases se não existir."""
    if not DATA_FILE.exists():
        print("📥 Baixando dados do GitHub Releases...")
        DATA_DIR.mkdir(exist_ok=True)
        
        try:
            response = requests.get(GITHUB_RELEASE_URL, stream=True)
            response.raise_for_status()
            
            # Verifica se é HTML (erro do GitHub)
            if "text/html" in response.headers.get("content-type", ""):
                raise Exception("Erro: Recebido HTML em vez de CSV")
            
            with open(DATA_FILE, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Arquivo baixado: {DATA_FILE.name}")
            
        except Exception as e:
            print(f"❌ Erro ao baixar: {e}")
            raise

def ensure_data_files():
    ensure_data_file()      # dados.csv
    ensure_cities_file()    # cidades.csv

app = FastAPI(title="Consulta de Rotas Logísticas", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "https://projeto-site-routelab.vercel.app"
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir frontend
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("startup")
async def startup_event():
    ensure_data_files()
    load_data()  # que carrega dados.csv
    load_cities_geo()  # nova função (veja abaixo)

from .database import CITIES_GEO

@app.get("/city-coords")
def get_city_coords():
    return CITIES_GEO

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse(content="<h1>Frontend não encontrado</h1>", status_code=404)
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/", response_model=dict)
def home():
    return {"message": "API de Consulta de Rotas"}

@app.get("/cities", response_model=CitiesResponse)
def get_cities():
    return {"cities": sorted(cities)}

@app.post("/route", response_model=RouteResponse)
def get_route(request: RouteRequest):
    key = f"{request.origin}-{request.destination}"
    route = db.get(key)
    if route:
        return RouteResponse(success=True, info=route)
    else:
        return RouteResponse(
            success=False,
            message=f"Rota não encontrada: {request.origin} → {request.destination}"
        )

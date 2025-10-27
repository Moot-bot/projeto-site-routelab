from fastapi import FastAPI, HTTPException, Request
from .database import load_data, load_cities_geo, db, cities, CITIES_GEO
from .schemas import RouteRequest, RouteResponse, CitiesResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import requests
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np

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
        "https://projeto-site-routelab.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir frontend
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates (para nova página)
templates = Jinja2Templates(directory=str(STATIC_DIR))

# Carregar DataFrame global (será usado pela nova rota)
df_global = None

@app.on_event("startup")
async def startup_event():
    global df_global
    ensure_data_files()
    load_data()  # carrega db e cities
    load_cities_geo()

    try:
        df_global = pd.read_csv(DATA_FILE, sep=";", encoding='latin1', decimal=',')
        print(f"✅ DataFrame global carregado com {len(df_global)} linhas.")
    except Exception as e:
        print(f"❌ Erro ao carregar DataFrame global: {e}")
        df_global = pd.DataFrame()
# === Rotas existentes (mantidas sem alteração) ===

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

# === Nova rota: Competitividade ===

@app.get("/competitividade", response_class=HTMLResponse)
async def serve_competitividade(request: Request):
    page_path = STATIC_DIR / "competitividade.html"
    if not page_path.exists():
        return HTMLResponse(content="<h1>Página de competitividade não encontrada</h1>", status_code=404)
    return templates.TemplateResponse("competitividade.html", {"request": request})

@app.get("/api/destinos/{origem}")
def get_destinos_competitividade(origem: str):
    global df_global
    if df_global is None or df_global.empty:
        raise HTTPException(status_code=500, detail="Dados de competitividade não carregados.")

    # Normalizar origem para busca
    origem_clean = origem.strip().lower()

    # Criar coluna auxiliar para busca robusta
    df_global['originName_clean'] = df_global['originName'].astype(str).str.strip().str.lower()

    # Filtrar com match exato primeiro
    mask_exact = df_global['originName_clean'] == origem_clean
    df_filtered = df_global[mask_exact].copy()

    if df_filtered.empty:
        # Tentar match parcial (substring)
        mask_partial = df_global['originName_clean'].str.contains(origem_clean, na=False)
        df_filtered = df_global[mask_partial].copy()
        if df_filtered.empty:
            raise HTTPException(status_code=404, detail=f"Origem '{origem}' não encontrada.")
        else:
            print(f"⚠️ Origem '{origem}' não encontrada exatamente. Usando correspondência parcial.")

    # Remover coluna auxiliar
    df_filtered = df_filtered.drop(columns=['originName_clean'], errors='ignore')

    # Limitar a 50 destinos
    df_filtered = df_filtered.head(50)

    # Garantir que colunas numéricas existam e sejam válidas
    required_cols = [
        'pathTotalCostWithoutBR319',
        'pathTotalCost2', 'pathTotalCostLG', 'pathTotalCostML', 'pathTotalCostNC',
        'originalCost', 'withBR319Cost',
        'pathEmissionWithoutBR319',
        'pathTransitTimeWithoutBR319'
    ]

    for col in required_cols:
        if col not in df_filtered.columns:
            raise HTTPException(status_code=500, detail=f"Coluna ausente: {col}")

    # Converter para numérico e tratar NaN/inf
    for col in required_cols:
        df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')
        df_filtered[col] = df_filtered[col].replace([np.inf, -np.inf], np.nan)

    # Remover linhas com custo rodoviário inválido
    df_filtered = df_filtered[
        df_filtered['pathTotalCostWithoutBR319'].notna() & 
        (df_filtered['pathTotalCostWithoutBR319'] > 0)
    ].copy()

    if df_filtered.empty:
        return {
            "abrangencia": 0,
            "economia_media": 0,
            "co2_media": 0,
            "tempo_medio": 0,
            "total_destinos": 0,
            "destinos_competitivos": 0,
            "top_economia": [],
            "corredores": [],
            "alerta_br319_count": 0,
            "alerta_br319_exemplos": []
        }

    # Calcular menor custo entre os 4 armadores
    cabotagem_cols = ['pathTotalCost2', 'pathTotalCostLG', 'pathTotalCostML', 'pathTotalCostNC']
    df_filtered['min_cabotagem'] = df_filtered[cabotagem_cols].min(axis=1, skipna=True)

    # Economia percentual
    df_filtered['economia_pct'] = np.where(
        df_filtered['pathTotalCostWithoutBR319'] > 0,
        (df_filtered['pathTotalCostWithoutBR319'] - df_filtered['min_cabotagem']) / df_filtered['pathTotalCostWithoutBR319'] * 100,
        np.nan
    )

    # Marcar como competitivo
    df_filtered['competitivo'] = df_filtered['economia_pct'] >= 10

    df_comp = df_filtered[df_filtered['competitivo']].copy()

    total_destinos = len(df_filtered)
    destinos_competitivos = len(df_comp)
    abrangencia_pct = (destinos_competitivos / total_destinos * 100) if total_destinos > 0 else 0
    economia_media = df_comp['economia_pct'].mean() if not df_comp.empty else 0

    # Redução de CO₂
    if not df_comp.empty:
        emissao_rodoviaria = df_comp['pathEmissionWithoutBR319']
        emissao_cabotagem = df_comp[['pathEmissionAL', 'pathEmissionLG', 'pathEmissionML', 'pathEmissionNC']].min(axis=1, skipna=True)
        delta_co2 = emissao_rodoviaria - emissao_cabotagem
        co2_media = delta_co2.mean() if not delta_co2.isna().all() else 0
    else:
        co2_media = 0

    # Aumento médio de tempo
    if not df_comp.empty:
        tempo_rodoviario = df_comp['pathTransitTimeWithoutBR319']
        tempo_cabotagem = df_comp[['pathTransitTimeAL', 'pathTransitTimeLG', 'pathTransitTimeML', 'pathTransitTimeNC']].min(axis=1, skipna=True)
        delta_tempo = tempo_cabotagem - tempo_rodoviario
        tempo_medio = delta_tempo.mean() if not delta_tempo.isna().all() else 0
    else:
        tempo_medio = 0

    # Top 10 economia
    top_economia = (
        df_filtered.nlargest(10, 'economia_pct')[
            ['destinationName', 'destinationUf', 'economia_pct']
        ].to_dict('records')
    )

    # Corredores estratégicos
    corredores = []
    if not df_comp.empty:
        df_comp['delta_co2'] = df_comp['pathEmissionWithoutBR319'] - df_comp[['pathEmissionAL', 'pathEmissionLG', 'pathEmissionML', 'pathEmissionNC']].min(axis=1, skipna=True)
        corredores_df = df_comp[df_comp['delta_co2'] >= 50]
        corredores = corredores_df.to_dict('records')

    # Alerta BR-319
    df_filtered['dif_br319_pct'] = np.where(
        df_filtered['originalCost'] > 0,
        (df_filtered['originalCost'] - df_filtered['withBR319Cost']) / df_filtered['originalCost'] * 100,
        np.nan
    )
    alerta_br319 = df_filtered[df_filtered['dif_br319_pct'] > 15].to_dict('records')

    return {
        "abrangencia": round(abrangencia_pct, 1),
        "economia_media": round(economia_media, 1) if pd.notna(economia_media) else 0,
        "co2_media": round(co2_media, 1) if pd.notna(co2_media) else 0,
        "tempo_medio": round(tempo_medio, 1) if pd.notna(tempo_medio) else 0,
        "total_destinos": total_destinos,
        "destinos_competitivos": destinos_competitivos,
        "top_economia": [
            {
                "destinationName": r["destinationName"],
                "destinationUf": r["destinationUf"],
                "economia_pct": round(r["economia_pct"], 1)
            }
            for r in top_economia if pd.notna(r.get("economia_pct"))
        ],
        "corredores": [
            {
                "destinationName": r["destinationName"],
                "destinationUf": r["destinationUf"],
                "economia_pct": round(r["economia_pct"], 1),
                "pathTransitTimeWithoutBR319": r["pathTransitTimeWithoutBR319"],
                "pathTransitTimeAL": r.get("pathTransitTimeAL"),
                "pathTransitTimeLG": r.get("pathTransitTimeLG"),
                "pathTransitTimeML": r.get("pathTransitTimeML"),
                "pathTransitTimeNC": r.get("pathTransitTimeNC"),
                "pathEmissionWithoutBR319": r["pathEmissionWithoutBR319"],
                "pathEmissionAL": r.get("pathEmissionAL"),
                "pathEmissionLG": r.get("pathEmissionLG"),
                "pathEmissionML": r.get("pathEmissionML"),
                "pathEmissionNC": r.get("pathEmissionNC"),
            }
            for r in corredores
        ],
        "alerta_br319_count": len(alerta_br319),
        "alerta_br319_exemplos": [r["destinationName"] for r in alerta_br319[:3]]
    }
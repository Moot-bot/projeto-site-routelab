import pandas as pd
from typing import Dict, Any
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = DATA_DIR / "dados.csv"

db: Dict[str, Dict[str, Any]] = {}
cities = set()

def parse_flag(value):
    if pd.isna(value):
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if str(value).strip().upper() in ("Y", "1", "TRUE", "SIM", "YES"):
        return True
    return False

CITIES_GEO = {}  # nodeName (ex: "Xinguara - PA") → { lat, lon, uf }

def load_cities_geo():
    global CITIES_GEO
    CITIES_PATH = DATA_DIR / "cidade.csv"
    
    if not CITIES_PATH.exists():
        print("⚠️ Arquivo cidade.csv não encontrado")
        return

    df = pd.read_csv(
        CITIES_PATH,
        sep=';',
        encoding='latin1',
        decimal=','
    )

    CITIES_GEO.clear()
    for _, row in df.iterrows():
        # ⬇️ CORREÇÃO PRINCIPAL: usar strip() no nodeName
        name = str(row['nodeName']).strip()
        CITIES_GEO[name] = {
            "lat": row['nodeLat'],
            "lon": row['nodeLon'],
            "uf": row['nodeUf']
        }
    print(f"🌍 Coordenadas de {len(CITIES_GEO)} cidades carregadas.")

def load_data():
    global db, cities
    print("Carregando dados do CSV...")

    if not CITIES_GEO:
        print("⚠️ Carregando coordenadas das cidades...")
        load_cities_geo()

    COLUNAS_NECESSARIAS = [
        'originName',
        'destinationName',
        'originUf',
        'destinationUf',
        'pathDistanceWithoutBR319',
        'pathTransitTimeWithoutBR319',
        'pathEmissionWithoutBR319',
        'pathEmissionAL',
        'pathEmissionLG',
        'pathEmissionML',
        'pathEmissionNC',
        'isAL10%',
        'isLG10%',
        'isML10%',
        'isNC10%',
        'pathTotalCostWithoutBR319',
        'pathTotalCost2',        # Armador AL
        'pathTotalCostLG',       # Armador LG
        'pathTotalCostML',       # Armador ML
        'pathTotalCostNC',       # Armador NC
        'originalCost',
        'withBR319Cost'
        ]

    df = pd.read_csv(
        CSV_PATH,
        usecols=COLUNAS_NECESSARIAS,
        low_memory=False,
        encoding='latin1',
        sep=';',
        decimal=','
    )
    colunas_custo = [
    'pathTotalCostWithoutBR319',
    'pathTotalCost2',
    'pathTotalCostLG',
    'pathTotalCostML',
    'pathTotalCostNC',
    'originalCost',
    'withBR319Cost'
]

    for col in colunas_custo:
        df[col] = pd.to_numeric(df[col], errors='coerce').astype('float32')
    colunas_numericas = [
        'pathDistanceWithoutBR319',
        'pathTransitTimeWithoutBR319',
        'pathEmissionWithoutBR319',
        'pathEmissionAL',
        'pathEmissionLG',
        'pathEmissionML',
        'pathEmissionNC',
    ]
    
    for col in colunas_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce').astype('float32')

    df.dropna(subset=['originName', 'destinationName'], inplace=True)

    db.clear()
    cities.clear()

    for _, row in df.iterrows():
        # ⬇️ CORREÇÃO: aplicar strip() nos nomes de origem e destino
        origem = str(row['originName']).strip()
        destino = str(row['destinationName']).strip()

        # Buscar coordenadas usando os nomes exatos (com UF, como "Xinguara - PA")
        origem_geo = CITIES_GEO.get(origem)
        destino_geo = CITIES_GEO.get(destino)

        if origem_geo is None:
            print(f"⚠️ Coordenadas não encontradas para origem: '{origem}'")
        if destino_geo is None:
            print(f"⚠️ Coordenadas não encontradas para destino: '{destino}'")

        # A chave usa os nomes exatos (como o frontend envia)
        key = f"{origem}-{destino}"

        db[key] = {
            "originName": origem,
            "destinationName": destino,
            "originUf": row.get("originUf"),
            "destinationUf": row.get("destinationUf"),
            "originLat": origem_geo["lat"] if origem_geo else None,
            "originLon": origem_geo["lon"] if origem_geo else None,
            "destinationLat": destino_geo["lat"] if destino_geo else None,
            "destinationLon": destino_geo["lon"] if destino_geo else None,
            "pathDistanceWithoutBR319": row.get("pathDistanceWithoutBR319"),
            "pathTransitTimeWithoutBR319": row.get("pathTransitTimeWithoutBR319"),
            "emissao_sem_br319": row.get("pathEmissionWithoutBR319"),
            "emissao_al": row.get("pathEmissionAL"),
            "emissao_lg": row.get("pathEmissionLG"),
            "emissao_ml": row.get("pathEmissionML"),
            "emissao_nc": row.get("pathEmissionNC"),
            "isAL10": parse_flag(row.get("isAL10%")),
            "isLG10": parse_flag(row.get("isLG10%")),
            "isML10": parse_flag(row.get("isML10%")),
            "isNC10": parse_flag(row.get("isNC10%")),
        }

        cities.add(origem)
        cities.add(destino)

    print(f"Dados carregados: {len(db)} rotas e {len(cities)} cidades.")

__all__ = ["load_data", "db", "cities", "load_cities_geo", "CITIES_GEO"]
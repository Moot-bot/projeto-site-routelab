import pandas as pd
import os
from typing import Dict, Any
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "dados.csv")

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

def load_data():
    global db, cities
    print("Carregando dados do CSV...")

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
    
]

    # 👇 Carrega SEM forçar dtype numérico (evita erros de conversão)
    df = pd.read_csv(
        CSV_PATH,
        usecols=COLUNAS_NECESSARIAS,
        low_memory=False,
        encoding='latin1',
        sep=';',
        decimal=','
    )

    # 👇 Converte colunas numéricas com segurança (ignora erros)
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

    # Remove linhas com origem/destino nulos
    df.dropna(subset=['originName', 'destinationName'], inplace=True)

    db.clear()
    cities.clear()

    for _, row in df.iterrows():
        origem = row['originName']
        destino = row['destinationName']
        key = f"{origem}-{destino}"

        db[key] = {
    "originUf": row.get("originUf"),
    "destinationUf": row.get("destinationUf"),
    "pathDistanceWithoutBR319": row.get("pathDistanceWithoutBR319"),
    "pathTransitTimeWithoutBR319": row.get("pathTransitTimeWithoutBR319"),
    
    # Emissões de CO₂ (em kg)
    "emissao_sem_br319": row.get("pathEmissionWithoutBR319"),
    "emissao_al": row.get("pathEmissionAL"),
    "emissao_lg": row.get("pathEmissionLG"),
    "emissao_ml": row.get("pathEmissionML"),
    "emissao_nc": row.get("pathEmissionNC"),

    # Flags de sustentabilidade (opcional)
    "isAL10": parse_flag(row.get("isAL10%")),
    "isLG10": parse_flag(row.get("isLG10%")),
    "isML10": parse_flag(row.get("isML10%")),
    "isNC10": parse_flag(row.get("isNC10%")),
    }

        cities.add(origem)
        cities.add(destino)

    print(f"Dados carregados: {len(db)} rotas e {len(cities)} cidades.")
# app/schemas.py

from pydantic import BaseModel
from typing import Optional, Dict, Any

class RouteRequest(BaseModel):
    origin: str
    destination: str

class RouteInfo(BaseModel):
    originUf: Optional[str]
    destinationUf: Optional[str]
    pathDistanceWithoutBR319: Optional[float]
    pathTransitTimeWithoutBR319: Optional[float]
    emissao_sem_br319: Optional[float]
    emissao_al: Optional[float]
    emissao_lg: Optional[float]
    emissao_ml: Optional[float]
    emissao_nc: Optional[float]
    isAL10: bool
    isLG10: bool
    isML10: bool
    isNC10: bool

    class Config:
        fields = {
            "isAL10": "isAL10%",
            "isLG10": "isLG10%",
            "isML10": "isML10%",
            "isNC10": "isNC10%"
        }

class RouteResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    info: Optional[RouteInfo] = None

class CitiesResponse(BaseModel):
    cities: list[str]
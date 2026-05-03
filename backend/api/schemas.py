from pydantic import BaseModel
from datetime import date


class CitySearchInput(BaseModel):
    query: str


class PredictionInput(BaseModel):
    culture: str
    zone: str
    latitude: float
    longitude: float
    engrais: float
    irrigation: str
    date_debut: date
    date_fin: date


class PredictionResponse(BaseModel):
    culture: str
    zone: str
    latitude: float
    longitude: float
    temperature: float
    humidite: float
    pluviometrie: float
    source_meteo: str
    type_sol: str
    ph: float
    engrais: float
    irrigation: str
    rendement_predit: float
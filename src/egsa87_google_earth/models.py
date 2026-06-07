from dataclasses import dataclass

@dataclass(frozen=True)
class Egsa87Coordinate:
    x: float
    y: float

@dataclass(frozen=True)
class Wgs84Coordinate:
    longitude: float
    latitude: float

@dataclass
class PointModel:
    x: float
    y: float
    longitude: float
    latitude: float
    name: str
    view_range: float

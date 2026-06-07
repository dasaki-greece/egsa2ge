from pyproj import Transformer
from ..models import Wgs84Coordinate, PointModel

# Μετασχηματισμός EPSG:2100 → EPSG:4326.
# always_xy=True σημαίνει ότι δίνουμε πάντα X,Y και παίρνουμε longitude,latitude.
_TRANSFORMER = Transformer.from_crs("EPSG:2100", "EPSG:4326", always_xy=True)

# Μετασχηματισμός EPSG:4326 → EPSG:2100.
_REVERSE_TRANSFORMER = Transformer.from_crs("EPSG:4326", "EPSG:2100", always_xy=True)


def transform_egsa87_to_wgs84(x: float, y: float) -> Wgs84Coordinate:
    """
    Transforms EGSA87 coordinates (X, Y) to WGS84 coordinates (longitude, latitude).
    """
    lon, lat = _TRANSFORMER.transform(x, y)
    return Wgs84Coordinate(longitude=lon, latitude=lat)


def transform_wgs84_to_egsa87(lon: float, lat: float) -> PointModel:
    """
    Transforms WGS84 coordinates (longitude, latitude) to EGSA87 coordinates (X, Y).
    """
    x, y = _REVERSE_TRANSFORMER.transform(lon, lat)
    return PointModel(x=x, y=y, longitude=lon, latitude=lat, name="Από Google Earth", view_range=800.0)

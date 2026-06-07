from xml.sax.saxutils import escape
from ..models import PointModel

def generate_saved_points_kml() -> str:
    """Generates the base KML for saved points."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Μόνιμα σημεία ΕΓΣΑ87</name>

    <Style id="savedPointStyle">
      <IconStyle>
        <scale>1.0</scale>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/paddle/blu-circle.png</href>
        </Icon>
      </IconStyle>
      <LabelStyle>
        <scale>0.8</scale>
      </LabelStyle>
    </Style>

  </Document>
</kml>
"""

def append_placemark_to_saved_points(kml_content: str, point: PointModel, timestamp: str) -> str:
    """Appends a new placemark to the existing saved points KML content."""
    safe_name = escape(point.name)

    description = (
        f"Χ ΕΓΣΑ87: {point.x:.3f}&lt;br/&gt;"
        f"Υ ΕΓΣΑ87: {point.y:.3f}&lt;br/&gt;"
        f"Longitude WGS84: {point.longitude:.8f}&lt;br/&gt;"
        f"Latitude WGS84: {point.latitude:.8f}&lt;br/&gt;"
        f"Καταχώριση: {timestamp}"
    )

    placemark = f"""
    <Placemark>
      <name>{safe_name}</name>
      <description>{description}</description>
      <styleUrl>#savedPointStyle</styleUrl>
      <Point>
        <coordinates>{point.longitude:.10f},{point.latitude:.10f},0</coordinates>
      </Point>
    </Placemark>
"""
    if "</Document>" not in kml_content:
        raise ValueError("Το saved_points.kml δεν έχει έγκυρη δομή KML.")

    return kml_content.replace("  </Document>", placemark + "\n  </Document>")

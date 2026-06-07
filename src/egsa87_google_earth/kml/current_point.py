from xml.sax.saxutils import escape
from ..models import PointModel

def generate_current_point_kml(point: PointModel, timestamp: str) -> str:
    """Generates the KML for the current point."""
    safe_name = escape(point.name)

    description = (
        f"Χ ΕΓΣΑ87: {point.x:.3f}&lt;br/&gt;"
        f"Υ ΕΓΣΑ87: {point.y:.3f}&lt;br/&gt;"
        f"Longitude WGS84: {point.longitude:.8f}&lt;br/&gt;"
        f"Latitude WGS84: {point.latitude:.8f}&lt;br/&gt;"
        f"Ενημέρωση: {timestamp}"
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Τρέχον σημείο ΕΓΣΑ87</name>

    <LookAt>
      <longitude>{point.longitude:.10f}</longitude>
      <latitude>{point.latitude:.10f}</latitude>
      <altitude>0</altitude>
      <range>{point.view_range:.2f}</range>
      <tilt>0</tilt>
      <heading>0</heading>
    </LookAt>

    <Style id="currentPointStyle">
      <IconStyle>
        <scale>0</scale>
      </IconStyle>
      <LabelStyle>
        <scale>0</scale>
      </LabelStyle>
    </Style>

    <Placemark>
      <name>{safe_name}</name>
      <description>{description}</description>
      <styleUrl>#currentPointStyle</styleUrl>
      <LookAt>
        <longitude>{point.longitude:.10f}</longitude>
        <latitude>{point.latitude:.10f}</latitude>
        <altitude>0</altitude>
        <range>{point.view_range:.2f}</range>
        <tilt>0</tilt>
        <heading>0</heading>
      </LookAt>
      <Point>
        <coordinates>{point.longitude:.10f},{point.latitude:.10f},0</coordinates>
      </Point>
    </Placemark>

  </Document>
</kml>
"""

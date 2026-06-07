def generate_empty_fly_to_kml() -> str:
    """Generates an empty fly-to KML."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <name>Μετάβαση στο τρέχον σημείο</name>
</Document>
</kml>
"""

def generate_fly_to_point_kml(longitude: float, latitude: float, view_range: float) -> str:
    """Generates the KML to trigger a fly-to in Google Earth."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <name>Μετάβαση στο τρέχον σημείο</name>

    <LookAt>
    <longitude>{longitude:.10f}</longitude>
    <latitude>{latitude:.10f}</latitude>
    <altitude>0</altitude>
    <range>{view_range:.2f}</range>
    <tilt>0</tilt>
    <heading>0</heading>
    </LookAt>

</Document>
</kml>
"""

def generate_network_link_kml(base_url: str) -> str:
    """Generates the KML for the network link using the local HTTP server."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <name>ΕΓΣΑ87 Live Link</name>


    <!-- Τοπικό Σταυρόνημα στην οθόνη του χρήστη -->
    <ScreenOverlay>
        <name>Στόχος (Σταυρόνημα)</name>
        <Icon>
            <href>{base_url}/crosshair.png</href>
        </Icon>
        <!-- Τοποθέτηση ακριβώς στο κέντρο της οθόνης -->
        <overlayXY x="0.5" y="0.5" xunits="fraction" yunits="fraction"/>
        <screenXY x="0.5" y="0.5" xunits="fraction" yunits="fraction"/>
        <rotationXY x="0" y="0" xunits="fraction" yunits="fraction"/>
        <size x="32" y="32" xunits="pixels" yunits="pixels"/>
    </ScreenOverlay>

    <NetworkLink>
        <name>Camera Tracking (Σταυρόνημα)</name>
        <visibility>1</visibility>
        <refreshVisibility>0</refreshVisibility>
        <flyToView>0</flyToView>
        <Link>
            <href>{base_url}/camera_update</href>
            <refreshMode>onChange</refreshMode>
            <viewRefreshMode>onStop</viewRefreshMode>
            <viewRefreshTime>0.5</viewRefreshTime>
            <viewFormat>BBOX=[bboxWest],[bboxSouth],[bboxEast],[bboxNorth]&amp;CAMERA=[cameraLon],[cameraLat]</viewFormat>
        </Link>
    </NetworkLink>

    <NetworkLink>
        <name>Τρέχον σημείο ΕΓΣΑ87</name>
        <visibility>1</visibility>
        <refreshVisibility>0</refreshVisibility>
        <flyToView>0</flyToView>
        <Link>
            <href>{base_url}/current.kml</href>
            <refreshMode>onInterval</refreshMode>
            <refreshInterval>1</refreshInterval>
        </Link>
    </NetworkLink>

    <NetworkLink>
        <name>Μετάβαση στο τρέχον σημείο</name>
        <visibility>1</visibility>
        <refreshVisibility>0</refreshVisibility>
        <flyToView>1</flyToView>
        <Link>
            <href>{base_url}/fly_to.kml</href>
            <refreshMode>onInterval</refreshMode>
            <refreshInterval>1</refreshInterval>
        </Link>
    </NetworkLink>

    <NetworkLink>
        <name>Μόνιμα σημεία ΕΓΣΑ87</name>
        <visibility>1</visibility>
        <refreshVisibility>0</refreshVisibility>
        <flyToView>0</flyToView>
        <Link>
            <href>{base_url}/saved.kml</href>
            <refreshMode>onInterval</refreshMode>
            <refreshInterval>3</refreshInterval>
        </Link>
    </NetworkLink>

</Document>
</kml>
"""

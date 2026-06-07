import tempfile
import platform
from pathlib import Path

APP_TITLE = "ΕΓΣΑ ’87 → Google Earth"
APP_VERSION = "1.0.0"
APP_EXE_NAME = f"EGSA2GE_Portable_v{APP_VERSION}"

# Φάκελος εργασίας. Χρησιμοποιούμε τον προσωρινό φάκελο του συστήματος για να μην αφήνουμε ίχνη.
DEFAULT_WORK_DIR = Path(tempfile.gettempdir()) / "Egsa2GE"

NETWORK_LINK_FILENAME = "egsa87_live_link.kml"
CURRENT_POINT_FILENAME = "current_point.kml"
SAVED_POINTS_FILENAME = "saved_points.kml"
FLY_TO_POINT_FILENAME = "fly_to_point.kml"


def get_work_dir() -> Path:
    return DEFAULT_WORK_DIR

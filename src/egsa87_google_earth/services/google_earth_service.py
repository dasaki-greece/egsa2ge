from pathlib import Path
from datetime import datetime
from typing import Callable, Optional, List
import logging

from ..models import PointModel
from ..core.coordinates import transform_egsa87_to_wgs84, transform_wgs84_to_egsa87
from ..kml.network_link import generate_network_link_kml
from ..kml.current_point import generate_current_point_kml
from ..kml.fly_to import generate_fly_to_point_kml, generate_empty_fly_to_kml
from ..kml.saved_points import generate_saved_points_kml, append_placemark_to_saved_points
from ..utils.platform_utils import open_path
from .file_service import FileService
from .http_server import LocalServer

class GoogleEarthService:
    def __init__(self, work_dir: Path) -> None:
        self.work_dir = work_dir
        self.log_file = work_dir / "ge_debug.log"
        self.last_poll_time = 0.0
        self.work_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=str(self.log_file),
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        logging.info("--- Google Earth Service Started ---")
        
        self.file_service = FileService(work_dir)
        self.network_link_path = work_dir / "egsa87_live_link.kml"
        
        self.server = LocalServer(port=8000, service=self)
        
        # State
        self.current_point: Optional[PointModel] = None
        self.current_point_timestamp: str = ""
        self.fly_to_point: Optional[PointModel] = None
        self.saved_points_kml_content: str = generate_saved_points_kml()
        self.camera_lon: float = 0.0
        self.camera_lat: float = 0.0
        
        self.on_camera_update_callback: Optional[Callable[[PointModel], None]] = None

    def initialize(self) -> None:
        """Initialize workspace, generate live link and start server."""
        self.file_service.ensure_work_dir()
        self.server.start()
        
        # Always write the network link to work_dir so the user can open it
        self.file_service.write_kml(self.network_link_path, self.generate_local_stub_link())

    def shutdown(self) -> None:
        self.server.stop()

    def set_camera_callback(self, callback: Callable[[PointModel], None]):
        self.on_camera_update_callback = callback

    def update_all_kmls(self, point: PointModel | None = None) -> None:
        """Updates the current point in memory."""
        if point is None:
            point = PointModel(
                x=0.0, y=0.0, longitude=22.0, latitude=40.0,
                name="Αρχικό σημείο", view_range=800.0
            )
        self.current_point = point
        self.current_point_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.fly_to_point = None  # clear fly-to

    def clear_fly_to(self) -> None:
        """Clears the fly-to point in memory."""
        logging.info("clear_fly_to: Fly-to point cleared.")
        self.fly_to_point = None

    def trigger_fly_to(self, point: PointModel) -> None:
        """Update current point and trigger the fly-to."""
        logging.info(f"trigger_fly_to: X={point.x:.2f}, Y={point.y:.2f}, Lon={point.longitude:.6f}, Lat={point.latitude:.6f}")
        self.current_point = point
        self.current_point_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.fly_to_point = point

    def add_saved_point(self, point: PointModel) -> None:
        """Adds a placemark to the saved points KML in memory."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.saved_points_kml_content = append_placemark_to_saved_points(
            self.saved_points_kml_content, point, timestamp
        )
        self.current_point = point
        self.current_point_timestamp = timestamp

    def on_camera_updated(self, lon: float, lat: float) -> None:
        """Called by the HTTP server when the camera stops moving."""
        logging.debug(f"on_camera_updated: Received from GE -> Lon={lon:.6f}, Lat={lat:.6f}")
        self.camera_lon = lon
        self.camera_lat = lat
        if self.on_camera_update_callback:
            # Transform WGS84 back to EGSA87
            try:
                point = transform_wgs84_to_egsa87(lon, lat)
                self.on_camera_update_callback(point)
            except Exception as e:
                logging.error(f"Transform error in on_camera_updated: {e}")
                print(f"Transform error: {e}")

    # HTTP Server KML Generators
    def generate_local_stub_link(self) -> str:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <NetworkLink>
    <name>ΕΓΣΑ87 Live Link</name>
    <open>1</open>
    <Link>
      <href>http://127.0.0.1:{self.server.port}/live_link.kml</href>
    </Link>
  </NetworkLink>
</kml>
"""

    def generate_live_network_link(self) -> str:
        base_url = f"http://127.0.0.1:{self.server.port}"
        return generate_network_link_kml(base_url)

    def get_current_point_kml(self) -> str:
        if self.current_point:
            return generate_current_point_kml(self.current_point, self.current_point_timestamp)
        return ""

    def get_fly_to_kml(self) -> str:
        if self.fly_to_point:
            kml = generate_fly_to_point_kml(
                self.fly_to_point.longitude, self.fly_to_point.latitude, self.fly_to_point.view_range
            )
            # Clear immediately after serving to prevent GE from re-triggering the flyTo animation
            self.fly_to_point = None
            logging.info("get_fly_to_kml: Served KML and cleared fly_to_point.")
            return kml
        return generate_empty_fly_to_kml()

    def get_saved_points_kml(self) -> str:
        return self.saved_points_kml_content

    def get_camera_target_kml(self) -> str:
        """Returns a placemark exactly at the camera center, updating live."""
        if self.camera_lon == 0.0 and self.camera_lat == 0.0:
            return ""
        
        try:
            pt = transform_wgs84_to_egsa87(self.camera_lon, self.camera_lat)
            desc = f"WGS84: {self.camera_lon:.6f}, {self.camera_lat:.6f}<br/>ΕΓΣΑ87: {pt.x:.3f}, {pt.y:.3f}"
        except:
            desc = "Out of bounds"

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <Placemark>
        <name>Κέντρο Οθόνης</name>
        <description><![CDATA[{desc}]]></description>
        <Style>
            <IconStyle>
                <scale>0</scale>
            </IconStyle>
            <LabelStyle>
                <scale>0</scale>
            </LabelStyle>
        </Style>
        <Point>
            <coordinates>{self.camera_lon},{self.camera_lat},0</coordinates>
        </Point>
    </Placemark>
</Document>
</kml>
"""

    def open_network_link_in_earth(self) -> None:
        open_path(self.network_link_path)

    def open_working_directory(self) -> None:
        open_path(self.work_dir)

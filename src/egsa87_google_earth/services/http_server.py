import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import sys
import logging
import time

class GoogleEarthHTTPRequestHandler(BaseHTTPRequestHandler):
    service = None  # Will be set by the server

    def log_message(self, format, *args):
        # Log HTTP requests to the debug file
        logging.debug(f"HTTP GET: {format%args}")

    def get_asset_path(self, filename: str) -> Path:
        if getattr(sys, 'frozen', False):
            assets_dir = Path(sys._MEIPASS) / "assets"
        else:
            assets_dir = Path(__file__).resolve().parent.parent.parent.parent / "assets"
        return assets_dir / filename

    def do_GET(self):
        # Update last poll time
        self.service.last_poll_time = time.time()
        
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == "/live_link.kml":
            self.send_kml(self.service.generate_live_network_link())
        elif path == "/current.kml":
            self.send_kml(self.service.get_current_point_kml())
        elif path == "/fly_to.kml":
            kml = self.service.get_fly_to_kml()
            logging.debug(f"Serving /fly_to.kml. Length: {len(kml)}")
            self.send_kml(kml)
        elif path == "/saved.kml":
            self.send_kml(self.service.get_saved_points_kml())
        elif path == "/camera_update":
            # Parse query parameters. Google Earth might use ';' as a separator.
            query_string = parsed_path.query.replace(";", "&")
            query_components = urllib.parse.parse_qs(query_string)
            camera = query_components.get("CAMERA", [""])[0]
            if camera:
                try:
                    lon_str, lat_str = camera.split(",")
                    lon = float(lon_str)
                    lat = float(lat_str)
                    self.service.on_camera_updated(lon, lat)
                except Exception as e:
                    logging.error(f"Failed to parse camera: {e}")
            
            # Send back the crosshair overlay and a placemark at the center
            self.send_kml(self.service.get_camera_target_kml())

        elif path in ["/icon02.png", "/crosshair.png"]:
            file_path = self.get_asset_path(path.strip("/"))
            if file_path.exists():
                self.send_response(200)
                self.send_header("Content-type", "image/png")
                self.send_header("Content-Length", str(file_path.stat().st_size))
                self.send_header("Connection", "close")
                self.end_headers()
                try:
                    with open(file_path, "rb") as f:
                        self.wfile.write(f.read())
                except Exception as e:
                    logging.debug(f"Connection dropped by GE while writing image: {e}")
            else:
                self.send_error(404, "File not found")
        else:
            self.send_error(404, "File not found")

    def send_kml(self, content: str):
        self.send_response(200)
        self.send_header("Content-type", "application/vnd.google-earth.kml+xml")
        # Ensure correct encoding
        encoded_content = content.encode("utf-8")
        self.send_header("Content-Length", str(len(encoded_content)))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(encoded_content)
        except Exception as e:
            logging.debug(f"Connection dropped by GE while writing: {e}")

class LocalServer:
    def __init__(self, port: int, service):
        self.port = port
        self.service = service
        self.server = None
        self.thread = None

    def start(self):
        GoogleEarthHTTPRequestHandler.service = self.service
        
        try:
            self.server = HTTPServer(("127.0.0.1", self.port), GoogleEarthHTTPRequestHandler)
        except OSError:
            # Fallback to a random port if 8000 is taken
            self.server = HTTPServer(("127.0.0.1", 0), GoogleEarthHTTPRequestHandler)
            self.port = self.server.server_port
            
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1)

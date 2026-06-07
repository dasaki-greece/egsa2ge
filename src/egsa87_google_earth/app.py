from .services.google_earth_service import GoogleEarthService
from .ui.main_window import MainWindow
from .config import DEFAULT_WORK_DIR

def main() -> None:
    service = GoogleEarthService(DEFAULT_WORK_DIR)
    app = MainWindow(service)
    app.mainloop()

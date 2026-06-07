import base64
from pathlib import Path


class FileService:
    def __init__(self, work_dir: Path) -> None:
        self.work_dir = work_dir
        self.work_dir = work_dir

    def ensure_work_dir(self) -> None:
        """Creates the work directory and its assets folder, generating the logo if missing."""
        self.work_dir.mkdir(parents=True, exist_ok=True)


    def write_kml(self, file_path: Path, content: str) -> None:
        """Writes string content to a file."""
        file_path.write_text(content, encoding="utf-8")

    def read_kml(self, file_path: Path) -> str:
        """Reads string content from a file."""
        return file_path.read_text(encoding="utf-8")

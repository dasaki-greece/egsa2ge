import platform
import subprocess
import os
import winreg
from pathlib import Path

def is_google_earth_installed() -> bool:
    """
    Ελέγχει αν το Google Earth είναι εγκατεστημένο (ή υπάρχει default handler για .kml)
    """
    if platform.system() != "Windows":
        return True
        
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r".kml") as key:
            return True
    except OSError:
        pass
        
        
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"GoogleEarth.kmlfile\shell\open\command"):
            return True
    except OSError:
        pass
        
    return False

def is_google_earth_running() -> bool:
    """Checks if googleearth.exe or googleearthpro.exe is currently running."""
    if platform.system() != "Windows":
        return False
        
    try:
        output = subprocess.check_output(
            'tasklist /FI "IMAGENAME eq googleearth.exe"', 
            shell=True, 
            text=True
        )
        if "googleearth.exe" in output.lower():
            return True
            
        output = subprocess.check_output(
            'tasklist /FI "IMAGENAME eq googleearthpro.exe"', 
            shell=True, 
            text=True
        )
        if "googleearthpro.exe" in output.lower():
            return True
            
        return False
    except Exception:
        return False

def launch_google_earth_empty() -> bool:
    """Launches Google Earth without opening any specific file."""
    if platform.system() != "Windows":
        return False
        
    try:
        # Get path from registry
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"GoogleEarth.kmlfile\shell\open\command") as key:
            command, _ = winreg.QueryValueEx(key, "")
            
        # Command is usually like: "C:\path\to\googleearth.exe" "%1"
        # We want just the executable path
        import shlex
        parts = shlex.split(command)
        if parts:
            exe_path = parts[0]
            subprocess.Popen([exe_path])
            return True
    except Exception as e:
        print(f"Could not launch GE from registry: {e}")
        pass
        
    return False

def open_path(path: Path) -> None:
    """
    Opens a file or directory using the default OS application.
    """
    path = path.resolve()
    if platform.system() == "Windows":
        os.startfile(path)  # type: ignore[attr-defined]
    elif platform.system() == "Darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)

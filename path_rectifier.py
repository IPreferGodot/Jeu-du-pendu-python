import sys
import os.path as os_path

def resource_path(relative_path: str) -> str:
    """Change path of ressources for .exe version"""
    try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS  # type: ignore
    except Exception:
        base_path = os_path.abspath(".")

    return os_path.join(base_path, *relative_path.split("\\"))
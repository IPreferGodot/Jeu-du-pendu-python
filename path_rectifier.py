import sys
import os.path as os_path

BUNDLED = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def split_path(string: str) -> list[str]:
    """Sépare au niveau des slash et des backslash, afin de ne pas les mélanger dans les chemins."""
    result = []
    for sub_string in string.split("/"):
        for sub_sub_string in sub_string.split("\\"):
            result.append(sub_sub_string)
    return result

def resource_path(relative_path: str) -> str:
    """Change path of ressources for .exe version"""
    return os_path.join(sys._MEIPASS if BUNDLED else os_path.abspath("."), *split_path(relative_path))
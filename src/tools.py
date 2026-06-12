import sys
import os

def resource_path(*relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS2 # type: ignore
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, *relative_path)

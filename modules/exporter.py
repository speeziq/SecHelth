import json
import os
from datetime import datetime

from .errors import ToolError


def save_results(history: list, folder: str = "results") -> str:
    if not history:
        raise ToolError("Nothing to save yet. Run a lookup first.")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"results_{datetime.now():%Y%m%d_%H%M%S}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, default=str, ensure_ascii=False)
    except OSError as e:
        raise ToolError(f"Could not write the file: {e}")
    return os.path.abspath(path)

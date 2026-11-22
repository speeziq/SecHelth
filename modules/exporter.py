import json
import csv
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


def save_results_csv(history: list, folder: str = "results") -> str:
    if not history:
        raise ToolError("Nothing to save yet. Run a lookup first.")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"results_{datetime.now():%Y%m%d_%H%M%S}.csv")
    try:
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "action", "target", "result"])
            for item in history:
                writer.writerow([
                    item.get("time", ""),
                    item.get("action", ""),
                    item.get("target", ""),
                    json.dumps(item.get("result", ""), ensure_ascii=False, default=str),
                ])
    except OSError as e:
        raise ToolError(f"Could not write the CSV file: {e}")
    return os.path.abspath(path)

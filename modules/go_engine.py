import json
import shutil
import subprocess
from pathlib import Path

from .errors import ToolError


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = PROJECT_ROOT / "engine"
ENGINE_BINARY = ENGINE_DIR / ("sechelth-engine.exe" if shutil.which("cmd") else "sechelth-engine")


def build_go_engine() -> str:
    if shutil.which("go") is None:
        raise ToolError("Go is not installed. The Python fallback engine is active.")
    try:
        subprocess.run(
            ["go", "build", "-o", str(ENGINE_BINARY), "."],
            cwd=str(ENGINE_DIR),
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        raise ToolError("Building the Go engine timed out.")
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "unknown build error").strip()
        raise ToolError(f"Could not build the Go engine: {detail}")
    return str(ENGINE_BINARY)


def get_go_engine() -> str:
    if ENGINE_BINARY.exists():
        return str(ENGINE_BINARY)
    return build_go_engine()


def run_go_engine(command: str, arguments: list[str]) -> dict:
    try:
        binary = get_go_engine()
        completed = subprocess.run(
            [binary, command, *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ToolError(f"Go engine could not run: {exc}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        detail = (completed.stderr or completed.stdout or "invalid engine response").strip()
        raise ToolError(f"Go engine returned an invalid response: {detail}")
    if completed.returncode != 0 or not payload.get("ok"):
        raise ToolError(payload.get("error") or "The Go engine failed.")
    return payload

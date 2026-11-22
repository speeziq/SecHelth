import requests

from .errors import ToolError


def get_http_info(target: str) -> dict:
    target = (target or "").strip()
    if not target:
        raise ToolError("Input is empty. Please enter a domain or URL.")
    url = target if "://" in target else "https://" + target
    try:
        r = requests.get(url, timeout=8, allow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 (Seccelth recon tool)"})
    except requests.exceptions.SSLError:
        raise ToolError("SSL error while connecting. The certificate may be invalid.")
    except requests.exceptions.ConnectionError:
        raise ToolError("Could not connect. Check the domain and your internet connection.")
    except requests.exceptions.Timeout:
        raise ToolError("The request timed out.")
    except requests.exceptions.RequestException as e:
        raise ToolError(f"Request failed: {e}")
    return {
        "status": f"{r.status_code} {r.reason}",
        "final_url": r.url,
        "redirects": [f"{h.status_code} -> {h.url}" for h in r.history],
        "response_time_ms": int(r.elapsed.total_seconds() * 1000),
        "headers": dict(r.headers),
    }

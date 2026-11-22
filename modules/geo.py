import requests

from .errors import ToolError
from .resolver import get_ip_domain
from .utils import clean_domain, is_ip


def get_geolocation(target: str) -> dict:
    """IP geolocation via the free ip-api.com service (HTTP only on the free tier)."""
    host = clean_domain(target)
    ip = host if is_ip(host) else get_ip_domain(host)[0]
    fields = "status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", params={"fields": fields}, timeout=8)
        data = r.json()
    except requests.exceptions.RequestException:
        raise ToolError("Could not reach the geolocation service. Check your internet connection.")
    except ValueError:
        raise ToolError("Geolocation service returned an unexpected response.")
    if data.get("status") != "success":
        raise ToolError(f"Geolocation failed: {data.get('message', 'unknown error')}")
    data.pop("status", None)
    return data

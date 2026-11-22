import ipaddress
from urllib.parse import urlparse

from .errors import ToolError


def clean_domain(value: str) -> str:
    """Turn 'https://Example.com:8080/path' into 'example.com'.
    Also works for plain domains and IP addresses (IPv4 and IPv6)."""
    value = (value or "").strip()
    if not value:
        raise ToolError("Input is empty. Please enter a domain or IP address.")
    if "://" not in value:
        value = "//" + value
    host = urlparse(value).hostname or ""
    if not host:
        raise ToolError(f"Could not read a hostname from '{value.lstrip('/')}'.")
    return host.lower()


def is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False

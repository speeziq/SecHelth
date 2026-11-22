import socket

from .errors import ToolError
from .utils import clean_domain, is_ip


def get_ip_domain(target: str) -> list:
    """Resolve a domain to all of its IP addresses (IPv4 + IPv6)."""
    host = clean_domain(target)
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise ToolError(f"Could not resolve '{host}'. Check the spelling or your internet connection.")
    ips = []
    for info in infos:
        ip = info[4][0]
        if ip not in ips:
            ips.append(ip)
    return ips


def reverse_dns(target: str) -> dict:
    """IP address -> hostname."""
    ip = clean_domain(target)
    if not is_ip(ip):
        raise ToolError("Reverse DNS needs an IP address, not a domain.")
    try:
        name, aliases, _ = socket.gethostbyaddr(ip)
    except (socket.herror, socket.gaierror):
        raise ToolError(f"No reverse DNS (PTR) record found for {ip}.")
    return {"ip": ip, "hostname": name, "aliases": aliases}

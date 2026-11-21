import socket
from concurrent.futures import ThreadPoolExecutor

from .errors import ToolError
from .resolver import get_ip_domain
from .utils import clean_domain, is_ip

COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 80: "HTTP",
    110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB", 993: "IMAPS",
    995: "POP3S", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
    6379: "Redis", 8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB",
}


def parse_ports(text: str) -> list:
    """'' -> common ports, '1-1024' -> range, '22,80,443' -> list."""
    text = text.strip()
    if not text:
        return sorted(COMMON_PORTS)
    try:
        if "-" in text:
            start, end = (int(x) for x in text.split("-", 1))
            ports = list(range(start, end + 1))
        else:
            ports = [int(p) for p in text.split(",")]
    except ValueError:
        raise ToolError("Invalid ports. Use '22,80,443', a range like '1-1024', or press Enter.")
    if not ports or min(ports) < 1 or max(ports) > 65535:
        raise ToolError("Ports must be between 1 and 65535.")
    if len(ports) > 5000:
        raise ToolError("Please scan at most 5000 ports at a time.")
    return ports


def _check(ip: str, port: int, timeout: float):
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return port if s.connect_ex((ip, port)) == 0 else None


def scan_ports(target: str, ports: list, timeout: float = 1.0) -> dict:
    host = clean_domain(target)
    ip = host if is_ip(host) else get_ip_domain(host)[0]
    with ThreadPoolExecutor(max_workers=100) as pool:
        found = [p for p in pool.map(lambda p: _check(ip, p, timeout), ports) if p]
    open_ports = [{"port": p, "service": COMMON_PORTS.get(p, "unknown")} for p in sorted(found)]
    return {"host": host, "ip": ip, "ports_scanned": len(ports), "open_ports": open_ports}

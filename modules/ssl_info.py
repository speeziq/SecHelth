import socket
import ssl
from datetime import datetime, timezone

from .errors import ToolError
from .utils import clean_domain


def _flatten(name_tuples) -> dict:
    return {k: v for rdn in name_tuples for k, v in rdn}


def get_ssl_info(target: str, port: int = 443) -> dict:
    host = clean_domain(target)
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=6) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as tls:
                cert = tls.getpeercert()
                version = tls.version()
    except ssl.SSLCertVerificationError as e:
        raise ToolError(f"Certificate verification failed: {e.verify_message}")
    except (socket.timeout, TimeoutError):
        raise ToolError("Connection timed out.")
    except (socket.gaierror, ConnectionError, OSError) as e:
        raise ToolError(f"Could not connect to {host}:{port} ({e}).")

    expires = datetime.fromtimestamp(ssl.cert_time_to_seconds(cert["notAfter"]), tz=timezone.utc)
    starts = datetime.fromtimestamp(ssl.cert_time_to_seconds(cert["notBefore"]), tz=timezone.utc)
    days_left = (expires - datetime.now(timezone.utc)).days
    subject = _flatten(cert.get("subject", ()))
    issuer = _flatten(cert.get("issuer", ()))
    sans = [v for k, v in cert.get("subjectAltName", ()) if k == "DNS"]
    return {
        "host": host,
        "subject": subject.get("commonName"),
        "issuer": issuer.get("organizationName") or issuer.get("commonName"),
        "valid_from": starts.strftime("%Y-%m-%d"),
        "valid_until": expires.strftime("%Y-%m-%d"),
        "days_remaining": days_left,
        "tls_version": version,
        "alt_names": sans,
    }

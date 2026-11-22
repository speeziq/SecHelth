import dns.exception
import dns.resolver

from .errors import ToolError
from .utils import clean_domain

RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]


def get_dns(domain: str, rtype: str = "A") -> list:
    """Return all records of one type for a domain."""
    domain = clean_domain(domain)
    rtype = rtype.upper()
    if rtype not in RECORD_TYPES:
        raise ToolError(f"Unsupported record type '{rtype}'. Choose from: {', '.join(RECORD_TYPES)}")
    try:
        answers = dns.resolver.resolve(domain, rtype, lifetime=5)
    except dns.resolver.NXDOMAIN:
        raise ToolError(f"The domain '{domain}' does not exist.")
    except dns.resolver.NoAnswer:
        raise ToolError(f"'{domain}' has no {rtype} records.")
    except dns.resolver.NoNameservers:
        raise ToolError("No nameservers could answer the query.")
    except dns.exception.Timeout:
        raise ToolError("DNS query timed out. Check your internet connection.")
    return [r.to_text() for r in answers]


def get_all_dns(domain: str) -> dict:
    """Return every supported record type that exists for a domain."""
    results = {}
    for rtype in RECORD_TYPES:
        try:
            results[rtype] = get_dns(domain, rtype)
        except ToolError as e:
            message = str(e).lower()
            if "does not exist" in message or "timed out" in message or "could not resolve" in message:
                raise
    if not results:
        raise ToolError(f"No DNS records found for '{clean_domain(domain)}'.")
    return results

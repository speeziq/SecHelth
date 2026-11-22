from .errors import ToolError
from .utils import clean_domain, is_ip
 
try:
    import whois
except ImportError:  # pragma: no cover
    whois = None
 
# Two different PyPI packages install a module called "whois". Only
# "python-whois" has the whois() function we need.
WRONG_PACKAGE = whois is not None and not hasattr(whois, "whois")
 
 
def _fmt(value):
    if isinstance(value, (list, tuple, set)):
        items = []
        for v in value:
            s = str(v)
            if s not in items:
                items.append(s)
        return items if len(items) > 1 else (items[0] if items else None)
    return str(value) if value is not None else None
 
 
def get_whois(domain: str) -> dict:
    if whois is None:
        raise ToolError("python-whois is not installed. Run: pip install python-whois")
    if WRONG_PACKAGE:
        raise ToolError("The wrong 'whois' package is installed. Run: "
                        "pip uninstall whois python-whois -y  then  pip install python-whois")
    domain = clean_domain(domain)
    if is_ip(domain):
        raise ToolError("WHOIS here is for domain names, not IP addresses.")
    try:
        w = whois.whois(domain)
    except Exception as e:
        raise ToolError(f"WHOIS lookup failed: {e}")
    if not w or not w.get("domain_name"):
        raise ToolError(f"No WHOIS data found for '{domain}'.")
    fields = ["domain_name", "registrar", "creation_date", "expiration_date",
              "updated_date", "name_servers", "status", "emails", "org", "country"]
    return {f: _fmt(w.get(f)) for f in fields if w.get(f)}
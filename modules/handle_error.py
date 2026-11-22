"""Central error handling for SecHelth.
 
Usage:
    from modules.handle_error import handle_error, catch_errors, install_global_hook
 
    try:
        ...
    except Exception as e:
        handle_error(e, context="Port Scan")
 
Every exception is turned into a short, friendly message for the user, and the
full traceback is written to logs/sechelth_errors.log for debugging.
"""
import functools
import json
import logging
import os
import socket
import ssl
import sys
from logging.handlers import RotatingFileHandler
 
import dns.exception
import dns.resolver
import requests
from colorama import Fore
 
from .errors import ToolError
 
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "sechelth_errors.log")
 
_logger = None
 
 
def _get_logger() -> logging.Logger:
    """Create the file logger on first use. Never crashes if the disk is read-only."""
    global _logger
    if _logger is not None:
        return _logger
    logger = logging.getLogger("sechelth")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        handler = RotatingFileHandler(LOG_FILE, maxBytes=500_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(handler)
    except OSError:
        logger.addHandler(logging.NullHandler())  # logging is optional, the tool keeps working
    _logger = logger
    return logger
 
 
def describe_error(exc: BaseException) -> tuple:
    """Return (friendly_message, is_expected).
 
    is_expected=False means it is a bug or something unusual, so the full
    traceback is logged. Order matters: specific exceptions come before general ones.
    """
    # 1. Errors our own modules raise on purpose already have good messages.
    if isinstance(exc, ToolError):
        return str(exc), True
 
    # 2. DNS (dnspython)
    if isinstance(exc, dns.resolver.NXDOMAIN):
        return "That domain does not exist.", True
    if isinstance(exc, dns.resolver.NoAnswer):
        return "The domain has no records of that type.", True
    if isinstance(exc, dns.resolver.NoNameservers):
        return "No nameservers could answer the query.", True
    if isinstance(exc, dns.exception.Timeout):
        return "DNS query timed out. Check your internet connection.", True
 
    # 3. HTTP (requests) - subclasses first
    if isinstance(exc, requests.exceptions.SSLError):
        return "SSL error. The site's certificate may be invalid or expired.", True
    if isinstance(exc, requests.exceptions.Timeout):
        return "The request timed out. The server is slow or unreachable.", True
    if isinstance(exc, requests.exceptions.ConnectionError):
        return "Could not connect. Check the address and your internet connection.", True
    if isinstance(exc, requests.exceptions.InvalidURL):
        return "That URL is not valid.", True
    if isinstance(exc, requests.exceptions.HTTPError):
        return f"The server returned an error: {exc}", True
    if isinstance(exc, requests.exceptions.RequestException):
        return f"Request failed: {exc}", True
 
    # 4. SSL / sockets (SSLCertVerificationError is an OSError, so check it first)
    if isinstance(exc, ssl.SSLCertVerificationError):
        return f"Certificate verification failed: {exc.verify_message}", True
    if isinstance(exc, ssl.SSLError):
        return f"SSL/TLS error: {exc}", True
    if isinstance(exc, socket.gaierror):
        return "Could not resolve that host name. Check the spelling or your connection.", True
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return "Connection timed out.", True
    if isinstance(exc, ConnectionRefusedError):
        return "Connection refused. The port is closed or a firewall is blocking it.", True
    if isinstance(exc, ConnectionError):
        return "The connection was lost.", True
 
    # 5. Files / permissions
    if isinstance(exc, PermissionError):
        return "Permission denied. Try another folder or run with the right permissions.", True
    if isinstance(exc, FileNotFoundError):
        return f"File or folder not found: {exc.filename or exc}", True
    if isinstance(exc, OSError):
        return f"System error: {exc}", True
 
    # 6. Bad data / missing packages
    if isinstance(exc, json.JSONDecodeError):
        return "The service returned data that could not be read (invalid JSON).", True
    if isinstance(exc, ValueError):
        return f"Invalid value: {exc}", True
    if isinstance(exc, ImportError):
        name = getattr(exc, "name", None) or "a package"
        return f"Missing package '{name}'. Run: pip install -r requirements.txt", True
 
    # 7. Anything else is unexpected.
    return f"Unexpected error ({type(exc).__name__}). Details were saved to {LOG_FILE}", False
 
 
def handle_error(exc: BaseException, context: str = "", show: bool = True) -> str:
    """Log the error, print a friendly message, and return that message."""
    message, expected = describe_error(exc)
    label = f"[{context}] " if context else ""
    logger = _get_logger()
    if expected:
        logger.warning("%s%s: %s", label, type(exc).__name__, exc)
    else:
        logger.error("%s%s", label, type(exc).__name__, exc_info=exc)
    if show:
        print(f"{Fore.RED}Error: {message}")
    return message
 
 
def catch_errors(func=None, *, context: str = "", default=None):
    """Decorator: run the function, and on any error handle it and return `default`.
 
        @catch_errors(context="WHOIS")
        def do_whois(): ...
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except (KeyboardInterrupt, SystemExit):
                raise  # Ctrl+C and sys.exit must keep working
            except Exception as e:
                handle_error(e, context=context or f.__name__)
                return default
        return wrapper
    return decorator(func) if func is not None else decorator
 
 
def install_global_hook() -> None:
    """Last safety net: any exception that escapes everything is logged, not dumped."""
    def hook(exc_type, exc, tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return
        _get_logger().critical("Uncaught exception", exc_info=(exc_type, exc, tb))
        print(f"{Fore.RED}Fatal error: {exc_type.__name__}. Details saved to {LOG_FILE}")
    sys.excepthook = hook
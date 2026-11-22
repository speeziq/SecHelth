import html as html_lib
import re
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests

from .errors import ToolError


MAX_ASSETS = 150
MAX_FILE_SIZE = 5 * 1024 * 1024
CHUNK_SIZE = 64 * 1024


class _ResourceParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.resources = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        attribute = {
            "script": "src",
            "img": "src",
            "link": "href",
            "source": "src",
            "video": "src",
            "audio": "src",
            "iframe": "src",
        }.get(tag)
        if attribute and values.get(attribute):
            self.resources.append(values[attribute])


def _safe_name(url: str, content_type: str = "") -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if not path:
        name = "index"
    else:
        name = re.sub(r"[^A-Za-z0-9._/-]", "_", path)
        name = name.lstrip("/")
        name = "/".join(
            part for part in name.split("/")
            if part not in {"", ".", ".."}
        )
        if name.endswith("/"):
            name += "index"
    if "." not in Path(name).name:
        if "javascript" in content_type:
            name += ".js"
        elif "css" in content_type:
            name += ".css"
        elif "html" in content_type:
            name += ".html"
    return name


def _same_origin(first: str, second: str) -> bool:
    a = urlparse(first)
    b = urlparse(second)
    return (
        a.scheme in {"http", "https"}
        and b.scheme in {"http", "https"}
        and a.hostname == b.hostname
        and a.port == b.port
    )


def _download_file(session: requests.Session, url: str, output: Path) -> tuple[bool, str]:
    try:
        response = session.get(url, timeout=15, stream=True)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        length = int(response.headers.get("Content-Length", "0") or "0")
        if length > MAX_FILE_SIZE:
            return False, "skipped: file exceeds 5 MB limit"

        output.parent.mkdir(parents=True, exist_ok=True)
        downloaded = 0
        with output.open("wb") as file:
            for chunk in response.iter_content(CHUNK_SIZE):
                if not chunk:
                    continue
                downloaded += len(chunk)
                if downloaded > MAX_FILE_SIZE:
                    file.close()
                    output.unlink(missing_ok=True)
                    return False, "skipped: file exceeds 5 MB limit"
                file.write(chunk)
        return True, content_type
    except requests.RequestException as exc:
        return False, f"failed: {exc}"
    except OSError as exc:
        return False, f"failed to write file: {exc}"


def download_website(target: str, folder: str = None) -> dict:
    target = (target or "").strip()
    if not target:
        raise ToolError("Input is empty. Please enter a website URL.")
    url = target if "://" in target else "https://" + target
    url = urldefrag(url)[0]
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ToolError("Please enter a valid http or https website.")

    domain = re.sub(r"[^A-Za-z0-9.-]", "_", parsed.hostname)
    project_root = Path(__file__).resolve().parent.parent
    requested_folder = (
        Path(folder).expanduser()
        if folder
        else project_root / "downloads"
    )

    candidates = [requested_folder]
    fallback_folder = Path(tempfile.gettempdir()) / "SecHelth" / "downloads"
    if fallback_folder not in candidates:
        candidates.append(fallback_folder)

    root = None
    for candidate in candidates:
        candidate_root = candidate / domain
        try:
            candidate_root.mkdir(parents=True, exist_ok=True)
            root = candidate_root
            break
        except OSError:
            continue

    if root is None:
        raise ToolError(
            "Could not create the downloads folder. Check folder permissions "
            "or run the tool from a writable location."
        )
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (SecHelth website downloader)"})

    html = ""
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type.lower():
            raise ToolError("The target did not return an HTML page.")
        html = response.text
    except requests.RequestException as exc:
        raise ToolError(f"Could not download the website: {exc}")

    home_path = root / "index.html"
    try:
        home_path.write_text(html, encoding="utf-8")
    except OSError as exc:
        raise ToolError(f"Could not write the downloaded HTML file: {exc}")

    parser = _ResourceParser()
    parser.feed(html)
    queue = []
    seen = set()
    for reference in parser.resources:
        absolute = urldefrag(urljoin(url, html_lib.unescape(reference)))[0]
        if _same_origin(url, absolute) and absolute not in seen:
            seen.add(absolute)
            queue.append(absolute)

    # Extract CSS URLs from stylesheet files and inline style attributes.
    css_references = re.findall(r"url\(([^)]+)\)", html, flags=re.IGNORECASE)
    for reference in css_references:
        reference = reference.strip("\"'")
        absolute = urldefrag(urljoin(url, reference))[0]
        if _same_origin(url, absolute) and absolute not in seen:
            seen.add(absolute)
            queue.append(absolute)

    downloaded = []
    skipped = []
    for resource_url in queue[:MAX_ASSETS]:
        name = _safe_name(resource_url)
        output = root / name
        ok, detail = _download_file(session, resource_url, output)
        if ok:
            downloaded.append({"url": resource_url, "file": str(output)})
            if output.suffix.lower() == ".css":
                try:
                    css = output.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    css = ""
                for reference in re.findall(r"url\(([^)]+)\)", css, flags=re.IGNORECASE):
                    reference = reference.strip("\"'")
                    absolute = urldefrag(urljoin(resource_url, reference))[0]
                    if _same_origin(url, absolute) and absolute not in seen:
                        seen.add(absolute)
                        queue.append(absolute)
        else:
            skipped.append({"url": resource_url, "reason": detail})

    return {
        "domain": parsed.hostname,
        "source_url": url,
        "html_file": str(home_path.resolve()),
        "downloaded_assets": downloaded,
        "skipped_assets": skipped,
        "asset_count": len(downloaded),
    }

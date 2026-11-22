# SecHelth V2

SecHelth is a command-line domain and network lookup tool. It provides IP lookup, DNS records, reverse DNS, WHOIS data, geolocation, port scanning, SSL certificate details, HTTP headers, JSON/CSV exports, session history, and authorized website downloads.

Developed by **[@speeziq](https://github.com/speeziq)** | Discord: **speeziq**

## Features

| # | Option | Description |
|---|--------|-------------|
| 1 | IP Lookup | Resolves a domain to IPv4 and IPv6 addresses |
| 2 | DNS Records | Retrieves A, AAAA, MX, NS, TXT, CNAME, SOA, and other records |
| 3 | Reverse DNS | Finds hostnames associated with an IP address |
| 4 | WHOIS | Retrieves registrar, expiration, and name-server information |
| 5 | IP Geolocation | Retrieves country, city, ISP, and ASN information |
| 6 | Port Scanner | Scans common ports, custom lists, or port ranges |
| 7 | SSL Certificate | Retrieves issuer, expiration, remaining days, and TLS details |
| 8 | HTTP Headers | Retrieves status, redirects, response time, and headers |
| 9 | Save Results | Saves session results as JSON |
| 10 | Session History | Displays lookups performed during the current session |
| 11 | Export CSV | Exports session results as CSV |
| 12 | Download Website | Downloads HTML and same-origin CSS, JavaScript, and media assets |
| 0 | Exit | Closes the tool |

> Use this tool only for systems, domains, and websites that you own or have explicit permission to test or download.

## Requirements

- [Python 3.8 or newer](https://www.python.org/downloads/)
- An internet connection
- [Git](https://git-scm.com/downloads/) - optional, for cloning the repository
- [Go 1.20 or newer](https://go.dev/dl/) - optional, for rebuilding the fast Go port-scanner engine

Python is required. Go is optional.

## Download the Project

Using Git:

```powershell
git clone <REPOSITORY_URL>
cd sechelth
```

Replace `<REPOSITORY_URL>` with the actual repository URL.

Alternatively, download the project as a ZIP file, extract it, and open a terminal inside the extracted folder.

## Install Python

Download Python from:

- [Python for Windows](https://www.python.org/downloads/windows/)
- [Official Python installation guide](https://docs.python.org/3/using/windows.html)

During installation, enable **Add Python to PATH**.

Verify the installation:

```powershell
python --version
```

If `python` is not recognized, try:

```powershell
py --version
```

## Install the Dependencies

Open a terminal in the project folder and create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

Upgrade pip and install the requirements:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If `python` is unavailable, use `py` instead:

```powershell
py -m pip install -r requirements.txt
```

## Run the Tool

With the virtual environment activated:

```powershell
python main.py
```

Enter an option number, press Enter, and follow the prompts. The menu will return automatically after the configured pause.

## Usage Examples

### IP Lookup

Choose `1`, then enter:

```text
example.com
```

### DNS Records

Choose `2`, enter a domain, and enter a record type such as `MX`. Press Enter without a type to retrieve all supported DNS records.

### Port Scan

Choose `6`, enter a host, then provide:

```text
22,80,443
```

For a range:

```text
1-1024
```

Press Enter without a value to scan the common ports.

### Download a Website

Choose `12`, then enter a URL:

```text
https://example.com
```

The tool saves the HTML and same-origin resources. Files are limited to 5 MB each, and at most 150 resources are processed per download.

## Optional Go Engine

Download Go from:

- [Official Go downloads](https://go.dev/dl/)
- [Official Go installation guide](https://go.dev/doc/install)

Verify Go:

```powershell
go version
```

Build the Windows engine:

```powershell
cd engine
go mod tidy
go build -o sechelth-engine.exe main.go
cd ..
```

The executable is created at:

```text
engine\sechelth-engine.exe
```

The Python application automatically uses this executable when available. If it is missing or unavailable, it falls back to the Python implementation.

On Linux or macOS:

```bash
cd engine
go mod tidy
go build -o sechelth-engine main.go
cd ..
python3 main.py
```

## Output Locations

| Output | Default location |
|--------|------------------|
| JSON results | `results\` inside the project |
| CSV results | `results\` inside the project |
| Website downloads | `downloads\<domain>\` inside the project |

If the project folder is not writable, the website downloader may use a temporary fallback location inside the system TEMP directory.

## Project Structure

```text
sechelth/
├── main.py                 # Menu and application actions
├── requirements.txt        # Python dependencies
├── Readme                  # Project documentation
├── engine/
│   ├── main.go             # Go DNS and port-scanner engine
│   ├── go.mod
│   └── sechelth-engine.exe
└── modules/
    ├── banner.py           # Logo and menu
    ├── dns_lookup.py       # DNS queries
    ├── exporter.py         # JSON and CSV export
    ├── geo.py              # IP geolocation
    ├── http_info.py        # HTTP headers
    ├── port_scanner.py     # Port scanning
    ├── resolver.py         # Forward/reverse resolution
    ├── ssl_info.py         # SSL certificates
    ├── website_downloader.py
    └── whois_lookup.py     # WHOIS data
```

## Customization

Edit [modules/banner.py](modules/banner.py) to change:

- `COLUMNS`
- `GAP`
- `MARGIN`
- `TOP_PADDING`
- `BOTTOM_PADDING`
- `ANIMATE`
- `LOGO_DELAY`
- `MENU_DELAY`

Edit `PAUSE_SECONDS` in [main.py](main.py) to change the delay before returning to the menu.

## Troubleshooting

### `whois` package error

The `whois` package name is shared by different packages. This tool requires `python-whois`:

```powershell
python -m pip uninstall whois python-whois -y
python -m pip install python-whois
```

### Access is denied or Permission denied

Run the tool from a writable location. Do not use protected folders such as `C:\Program Files` or Windows system directories as the output location.

To reset the downloads folder:

```powershell
rmdir /s /q downloads
python main.py
```

You can also call the downloader with a specific writable folder:

```python
download_website("https://example.com", r"C:\Users\YourName\Downloads\SecHelth")
```

### Broken colors or box characters

Use Windows Terminal and set UTF-8 output:

```powershell
chcp 65001
python main.py
```

### Geolocation failures

The free `ip-api.com` service may rate-limit requests. Wait before retrying.

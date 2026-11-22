import time
from datetime import datetime
 
import colorama
from colorama import Fore
 
from modules.banner import clear_screen, play_banner
from modules.dns_lookup import RECORD_TYPES, get_all_dns, get_dns
from modules.handle_error import handle_error, install_global_hook
from modules.exporter import save_results, save_results_csv
from modules.geo import get_geolocation
from modules.http_info import get_http_info
from modules.port_scanner import parse_ports, scan_ports
from modules.resolver import get_ip_domain, reverse_dns
from modules.ssl_info import get_ssl_info
from modules.whois_lookup import get_whois
from modules.website_downloader import download_website
from colorama import Fore, ansi
colorama.init(autoreset=True)
 
history = []  # every successful lookup of this session
 
 
def ask(prompt: str) -> str:
    return input(f"{Fore.RED}{prompt}{Fore.RESET}").strip()
 
 
def show(data, indent: int = 0) -> None:
    pad = "  " * indent
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)) and value:
                print(f"{pad}{Fore.YELLOW}{key}:")
                show(value, indent + 1)
            else:
                print(f"{pad}{Fore.YELLOW}{key}: {Fore.GREEN}{value}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                show(item, indent)
                print()
            else:
                print(f"{pad}{Fore.GREEN}- {item}")
    else:
        print(f"{pad}{Fore.GREEN}{data}")
 
 
 
def do_ip():
    target = ask("Enter domain: ")
    return "IP Lookup", target, get_ip_domain(target)
 
 
def do_dns():
    target = ask("Enter domain: ")
    options = ", ".join(RECORD_TYPES)
    rtype = ask(f"Record type ({options}, or ALL) [ALL]: ").upper() or "ALL"
    result = get_all_dns(target) if rtype == "ALL" else {rtype: get_dns(target, rtype)}
    return "DNS Records", target, result
 
 
def do_reverse():
    target = ask("Enter IP address: ")
    return "Reverse DNS", target, reverse_dns(target)
 
 
def do_whois():
    target = ask("Enter domain: ")
    return "WHOIS", target, get_whois(target)
 
 
def do_geo():
    target = ask("Enter domain or IP: ")
    return "IP Geolocation", target, get_geolocation(target)
 
 
def do_ports():
    print(f"{Fore.YELLOW}Only scan hosts you own or have permission to test.")
    target = ask("Enter domain or IP: ")
    ports = parse_ports(ask("Ports (e.g. 22,80,443 or 1-1024) [Enter = common ports]: "))
    print("Scanning...")
    return "Port Scan", target, scan_ports(target, ports)
 
 
def do_ssl():
    target = ask("Enter domain: ")
    return "SSL Certificate", target, get_ssl_info(target)
 
 
def do_http():
    target = ask("Enter domain or URL: ")
    return "HTTP Headers", target, get_http_info(target)
 
 
def do_save():
    path = save_results(history)
    print(f"{Fore.GREEN}Saved {len(history)} result(s) to: {path}")
    return None
 
 
def do_save_csv():
    path = save_results_csv(history)
    print(f"{Fore.GREEN}Saved {len(history)} result(s) to: {path}")
    return None
 
 
def do_download_website():
    print(f"{Fore.YELLOW}Downloads HTML and same-origin CSS/JS/media resources.")
    print(f"{Fore.YELLOW}Use only websites you own or have permission to download.")
    target = ask("Enter website URL: ")
    result = download_website(target)
    print(f"{Fore.GREEN}Saved website source to: {result['html_file']}")
    return "Website Download", target, result
 
 
def do_history():
    if not history:
        print(f"{Fore.YELLOW}No results in this session yet.")
        return None
    print(f"{Fore.CYAN}Session history ({len(history)} lookup(s)):")
    for index, item in enumerate(history, 1):
        print(f"{Fore.YELLOW}{index}. {item['action']} -> {Fore.GREEN}{item['target']}")
    return None
 
 
ACTIONS = {
    "1": do_ip, "2": do_dns, "3": do_reverse, "4": do_whois, "5": do_geo,
    "6": do_ports, "7": do_ssl, "8": do_http, "9": do_save,
    "10": do_history, "11": do_save_csv, "12": do_download_website,
}
 
 
PAUSE_SECONDS = 3  # how long the result stays on screen before the menu returns
 
 
def pause() -> None:
    """Count down, then go back to the menu automatically. Ctrl+C skips the wait."""
    try:
        print()
        for left in range(PAUSE_SECONDS, 0, -1):
            print(f"\r{Fore.GREEN}{left} second{'s' if left != 1 else ''} to reset to menu...   ",
                  end="", flush=True)
            time.sleep(1)
        print()
    except KeyboardInterrupt:
        print()
 
 
def main() -> None:
    while True:
        print(ansi.set_title("SecHelth V2"), end="", flush=True)
        clear_screen()
        play_banner()
        action = None
        try:
            choice = ask("\n> Choose an option: ")
            if choice == "0":
                print("Goodbye!")
                return
            action = ACTIONS.get(choice)
            if action is None:
                print(f"{Fore.RED}Invalid option.")
                time.sleep(1)
                continue
            outcome = action()
            if outcome:
                name, target, result = outcome
                print()
                show(result)
                history.append({
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "action": name,
                    "target": target,
                    "result": result,
                })
            pause()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{Fore.RED}Interrupted. Goodbye!")
            return
        except Exception as e:
            handle_error(e, context=getattr(action, "__name__", "menu"))
            pause()
 
 
if __name__ == "__main__":
    install_global_hook()
    main()
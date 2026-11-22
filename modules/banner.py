import os
import sys
import time
 
from colorama import Fore, Style
 
LOGO = r"""

                              ____            _   _      _ _   _     
                             / ___|  ___  ___| | | | ___| | |_| |__  
                             \___ \ / _ \/ __| |_| |/ _ \ | __| '_ \ 
                              ___) |  __/ (__|  _  |  __/ | |_| | | |
                             |____/ \___|\___|_| |_|\___|_|\__|_| |_|
                                                                                              
                           ──────────────────────────────────────────────

                              Developed by: @speeziq | discord: speeziq
                            """                           
 
MENU_ITEMS = [
    ("1", "IP Lookup"),
    ("2", "DNS Records"),
    ("3", "Reverse DNS"),
    ("4", "WHOIS"),
    ("5", "IP Geolocation"),
    ("6", "Port Scanner"),
    ("7", "SSL Certificate"),
    ("8", "HTTP Headers"),
    ("9", "Save Results"),
    ("10", "Session History"),
    ("11", "Export CSV"),
    ("12", "Download Website"),
    ("0", "Exit"),
]
 
# ---- menu layout ---------------------------------------------------------
COLUMNS = 4         # 12 options in vertical columns (1 4 7 10)
GAP = 4             # spaces between columns
MARGIN = 2          # spaces between the border and the text (left and right)
TOP_PADDING = 1     # blank lines at the top of the box
BOTTOM_PADDING = 1  # blank lines at the bottom of the box
ROW_SPACING = 0     # blank lines between rows of options
EXIT_LEFT_SHIFT = 4  # moves 0. Exit slightly left of the exact center
 
# ---- animation -----------------------------------------------------------
ANIMATE = True        # set to False to show the banner instantly
LOGO_DELAY = 0.06     # seconds between logo lines
MENU_DELAY = 0.05     # seconds between menu lines
 
 
def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")
 
 
def menu_lines() -> list:
    """Menu across the width of the terminal, with perfectly even margins."""
    cells = [f"{key}. {label}" for key, label in MENU_ITEMS if key != "0"]
    rows_count = (len(cells) + COLUMNS - 1) // COLUMNS
    rows = [
        [cells[row + column * rows_count] if row + column * rows_count < len(cells) else "" for column in range(COLUMNS)]
        for row in range(rows_count)
    ]
 
    widths = [max(len(r[c]) for r in rows if c < len(r)) for c in range(COLUMNS)]
    inner = sum(widths) + GAP * (COLUMNS - 1) + 2 * MARGIN
 
    blank = f"{Fore.RED}│{' ' * inner}│"
    lines = [f"{Fore.RED}╭{'─' * inner}╮"]
    lines += [blank] * TOP_PADDING
    for n, row in enumerate(rows):
        if n > 0:
            lines += [blank] * ROW_SPACING
        text = (" " * GAP).join(
            (row[c] if c < len(row) else "").ljust(widths[c]) for c in range(COLUMNS)
        )
        lines.append(f"{Fore.RED}│{' ' * MARGIN}{Fore.WHITE}{text}{Fore.RED}{' ' * MARGIN}│")
    lines += [blank]  # extra space before Exit
    exit_text = "0. Exit"
    exit_left = max(0, (inner - len(exit_text)) // 2 - EXIT_LEFT_SHIFT)
    exit_right = inner - exit_left - len(exit_text)
    lines.append(
        f"{Fore.RED}│{Fore.WHITE}{' ' * exit_left}{exit_text}"
        f"{' ' * exit_right}{Fore.RED}│"
    )
    lines += [blank] * BOTTOM_PADDING
    lines.append(f"{Fore.RED}╰{'─' * inner}╯{Style.RESET_ALL}")
    return lines
 
 
def menu() -> str:
    return "\n".join(menu_lines())
 
 
def banner() -> str:
    """The whole banner as one string (no animation)."""
    return "\n".join(
        f"{Fore.RED}{line}{Style.RESET_ALL}"
        for line in LOGO.strip("\n").splitlines()
    )
 
 
def play_banner() -> None:
    if not ANIMATE or not sys.stdout.isatty():
        print(banner())
        return
 
    print()
    for line in LOGO.strip("\n").splitlines():
        print(f"{Fore.RED}{line}{Style.RESET_ALL}")
        time.sleep(LOGO_DELAY)
 
    print()
 
    for line in menu_lines():
        print(line)
        time.sleep(MENU_DELAY)
 
 
if __name__ == "__main__":
    clear_screen()
    play_banner()
 
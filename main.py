import os
import sys
import time
import random
import string
import threading
import argparse
import requests
from concurrent.futures import ThreadPoolExecutor

url = "https://files.catbox.moe/"

DEFAULT_EXTENSIONS = [
    ".vpk",
    ".vtf",
    ".bsp",
]

urls_checked = 0
hits_found = 0
files_saved = 0
start_time = 0

running = True
lock = threading.Lock()
log_lock = threading.Lock()
log_file = None

def rdm_str(len_chars: int = 6) -> str:
    charset = string.ascii_lowercase + string.digits
    return "".join(random.choice(charset) for _ in range(len_chars))

def save(folder: str, filename: str, data: bytes) -> bool:
    try:
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
        with open(path, "wb") as f:
            f.write(data)
        return True
    except Exception:
        return False

def hits_log(hit_url: str) -> None:
    with log_lock:
        log_file.write(hit_url + "\n")
        log_file.flush()

def timer(seconds: int) -> str:
    hours, rem = divmod(seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def dashboard() -> None:
    with lock:
        elapsed = int(time.time() - start_time)
        local_urls_checked = urls_checked
        local_hits_found = hits_found
        local_files_saved = files_saved

    per_sec = local_urls_checked // elapsed if elapsed > 0 else 0

    sys.stdout.write("\033[H")

    print("┌────────────────────────────────────────┐")
    print("│              CATBOX SCRAPER            │")
    print("├────────────────────────────────────────┤")
    print("│                BY DOOT                 │")
    print("│            UPDATED VERSION             │")
    print("└────────────────────────────────────────┘")

    print("┌────────────────────────────────────────┐")
    print("│               MAIN STATS               │")
    print("├────────────────────────────────────────┤")
    print(f"│ TIME ELAPSED : {timer(elapsed):<23} │")
    print(f"│ CHECKS       : {local_urls_checked:<23} │")
    print(f"│ HITS         : {local_hits_found:<23} │")
    print(f"│ SAVED        : {local_files_saved:<23} │")
    print(f"│ PER SECOND   : {per_sec:<23} │")
    print("└────────────────────────────────────────┘")

def make_session(headers: dict) -> requests.Session:
    session = requests.Session()
    session.headers.update(headers)
    return session

def worker(headers: dict, extensions: list) -> None:
    global urls_checked, hits_found, files_saved, running

    session = make_session(headers)

    while running:
        for ext in extensions:
            if not running:
                break

            filename = rdm_str() + ext
            full_url = url + filename

            with lock:
                urls_checked += 1

            try:
                time.sleep(random.uniform(0.1, 0.3))
                response = session.get(full_url, timeout=10)
            except requests.RequestException:
                continue

            if response.status_code == 200:
                hits_log(full_url)

                with lock:
                    hits_found += 1

                folder = ext.lstrip(".")
                success = save(folder, filename, response.content)

                if success:
                    with lock:
                        files_saved += 1

def main() -> None:
    global running, start_time, log_file

    parser = argparse.ArgumentParser(description="Catbox scraper")
    parser.add_argument("--threads", type=int, default=32,
                        help="Number of worker threads (default: 32)")
    parser.add_argument("--update-rate", type=float, default=0.25,
                        help="Dashboard refresh rate in seconds (default: 0.25)")
    parser.add_argument("--extensions", nargs="+", default=DEFAULT_EXTENSIONS,
                        help="File extensions to search (e.g. .png .mp4)")
    args = parser.parse_args()

    extensions = [e if e.startswith(".") else f".{e}" for e in args.extensions]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 15; Pixel 9 Pro Build/AP4A.250405.002; wv) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
            "Chrome/135.0.7049.111 Mobile Safari/537.36"
        ),
        "Accept": "*/*",
    }

    start_time = time.time()

    os.system("")
    sys.stdout.write("\033[2J")

    last_update = 0

    with open("hits.log", "a", encoding="utf-8") as f:
        log_file = f

        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            for _ in range(args.threads):
                executor.submit(worker, headers, extensions)

            try:
                while running:
                    now = time.time()
                    if now - last_update >= args.update_rate:
                        dashboard()
                        last_update = now
                    time.sleep(0.01)
            except KeyboardInterrupt:
                running = False
                time.sleep(0.2)
                sys.stdout.write("\033[?25h")
                print("\nStopped.")

if __name__ == "__main__":
    sys.stdout.write("\033[?25l")
    try:
        main()
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

import os
import math
import time
import threading
import secrets
import string
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from .file_md5 import file_md5

CHUNK_SIZE = 131072
LOCK = threading.Lock()
CHUNK_RETRY_LIMIT = 3

def format_seconds(sec: float) -> str:
    sec = int(sec)
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def download_range(url: str, start: int, end: int, temp_path: str, progress: list):
    current_pos = start
    remaining_start = start
    remaining_end = end

    while remaining_start <= remaining_end:
        headers = {
            "User-Agent": "Python/3.x",
            "Range": f"bytes={remaining_start}-{remaining_end}"
        }
        req = Request(url, headers=headers)
        retry_count = 0
        success = False

        while retry_count < CHUNK_RETRY_LIMIT and not success:
            try:
                with urlopen(req, timeout=30) as resp:
                    while chunk := resp.read(CHUNK_SIZE):
                        chunk_len = len(chunk)
                        with LOCK:
                            with open(temp_path, "rb+") as f:
                                f.seek(current_pos)
                                f.write(chunk)
                            progress[0] += chunk_len
                        current_pos += chunk_len
                        remaining_start += chunk_len
                    success = True
            except (URLError, TimeoutError, OSError):
                retry_count += 1
                if retry_count >= CHUNK_RETRY_LIMIT:
                    return False
        if not success:
            return False
    return True

def download_file(url: str, save_path: str, n_threads: int = 16) -> bool:
    if os.path.isfile(save_path):
        os.remove(save_path)

    # Generate random string (letters, digits, underscore)
    rand_str = ''.join(secrets.choice(string.ascii_letters + string.digits + '_') for _ in range(12))
    # Temp file format: save_path.random_string.tmp
    temp_path = f"{save_path}.{rand_str}.tmp"
    start_time = time.time()

    try:
        support_parallel = False
        file_size = -1

        try:
            req = Request(url, headers={"User-Agent": "Python/3.x"}, method="HEAD")
            with urlopen(req, timeout=10) as resp:
                cl = resp.headers.get("Content-Length")
                accept_ranges = resp.headers.get("Accept-Ranges", "")
                if cl and accept_ranges.lower() == "bytes":
                    file_size = int(cl)
                    support_parallel = True
        except:
            pass

        if not support_parallel or file_size <= 0:
            req = Request(url, headers={"User-Agent": "Python/3.x"})
            with urlopen(req, timeout=30) as resp, open(temp_path, "wb") as f:
                byte_read = 0
                now_rate = ""

                if resp.status != 200:
                    raise HTTPError(url, resp.status, "Request failed", resp.headers, None)

                while chunk := resp.read(CHUNK_SIZE):
                    byte_read += len(chunk)
                    if file_size > 0:
                        percent = math.floor(byte_read / file_size * 100)
                        elapsed = time.time() - start_time
                        speed = byte_read / elapsed if elapsed > 0 else 0
                        remaining = (file_size - byte_read) / speed if speed > 0 else 0
                        elapsed_str = format_seconds(elapsed)
                        remain_str = format_seconds(remaining)
                        new_rate = f"{percent:4d}% ({elapsed_str} ETA:{remain_str}) (multithread not available)"
                        if new_rate != now_rate:
                            now_rate = new_rate
                            print(f"\r\033[1;34mdownloading\033[0m:{new_rate}", flush=True, end="")
                    f.write(chunk)
        else:
            progress = [0]
            now_rate = ""

            with open(temp_path, "wb") as f:
                f.seek(file_size - 1)
                f.write(b"\0")

            part_size = file_size // n_threads
            ranges = []
            for i in range(n_threads):
                s = i * part_size
                e = s + part_size - 1 if i < n_threads - 1 else file_size - 1
                ranges.append((s, e))

            with ThreadPoolExecutor(max_workers=n_threads) as executor:
                futures = [
                    executor.submit(download_range, url, s, e, temp_path, progress)
                    for s, e in ranges
                ]

                while True:
                    total_downloaded = progress[0]
                    percent = math.floor(total_downloaded / file_size * 100)

                    elapsed = time.time() - start_time
                    speed = total_downloaded / elapsed if elapsed > 0 else 0
                    remaining = (file_size - total_downloaded) / speed if speed > 0 else 0

                    elapsed_str = format_seconds(elapsed)
                    remain_str = format_seconds(remaining)

                    new_rate = f"{percent:4d}% ({elapsed_str} ETA:{remain_str}) ({n_threads} threads)"
                    if new_rate != now_rate:
                        now_rate = new_rate
                        print(f"\r\033[1;34mdownloading\033[0m:{new_rate}", flush=True, end="")

                    if all(f.done() for f in futures):
                        break

                if not all(f.result() for f in futures):
                    raise OSError("Parallel download failed: one or more parts failed")

        os.rename(temp_path, save_path)
        elapsed_total = time.time() - start_time
        elapsed_str = format_seconds(elapsed_total)
        print("\r{ ' ' * 60 }\r", end="", flush=True)
        print("\r" + (" " * 60) +  "\r" + f"\033[1;34mdownloading\033[0m: 100% ({elapsed_str})", flush=True)
        return True

    except (URLError, HTTPError, OSError, TimeoutError) as e:
        print(f"\n\033[1;31mdownload failed\033[0m: {str(e)}")
        return False
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def remote_auto_fetch(
    url: str,
    save_path: str,
    md5_hash: Optional[str] = None,
    max_try: int = 5,
    n_threads: int = 16
):
    n_threads = max(n_threads, 1)

    file_dir = os.path.dirname(os.path.abspath(save_path))
    os.makedirs(file_dir, exist_ok=True)

    if not os.path.isfile(save_path) or (
        md5_hash is not None and file_md5(save_path) != md5_hash.lower()
    ):
        print(f"\033[1;34mdownloading\033[0m: {url} ...")
        success = download_file(url, save_path, n_threads=n_threads)
        max_try -= 1

        while not success and max_try > 0:
            success = download_file(url, save_path, n_threads=n_threads)
            max_try -= 1

        if not success:
            print(f"\033[1;31mdownload failed\033[0m: maximum retry attempts exceeded")

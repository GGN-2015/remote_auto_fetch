import os
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from typing import Optional
import math
from .file_md5 import file_md5

def download_file(url: str, save_path: str) -> bool:

    # Remove existing file first
    if os.path.isfile(save_path):
        os.remove(save_path)

    # Temporary file (avoid leaving empty file if download fails)
    temp_path = f"{save_path}.tmp"
    
    try:
        # Construct request (add User-Agent to avoid being blocked)
        req = Request(url, headers={"User-Agent": "Python/3.x"})
        # Open connection and download in chunks
        with urlopen(req, timeout=30) as resp, open(temp_path, "wb") as f:
            content_length = resp.headers.get("Content-Length")
            content_length = int(content_length) if content_length else -1  # File length unknown
            byte_read = 0
            now_rate  = "\033[1;34mdownloading\033[0m:   0%"  # Current progress percentage

            # Check response status
            if resp.status != 200:
                raise HTTPError(url, resp.status, "Request failed", resp.headers, None)
            
            # Write to temporary file in chunks
            while chunk := resp.read(16384):
                byte_read += len(chunk)

                if content_length > 0:
                    new_rate = f"{math.floor(byte_read / content_length * 100):4d}%"
                    if new_rate != now_rate:
                        now_rate = new_rate
                        print(f"\r\033[1;34mdownloading\033[0m:{now_rate}\r", flush=True, end="")
                f.write(chunk)
        
        # Download completed, rename temp file to target file
        os.rename(temp_path, save_path)
        return True
    
    except (URLError, HTTPError, OSError, TimeoutError) as e:
        print(f"\033[1;31mdownload failed\033[0m: {e}")
        return False
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

def remote_auto_fetch(url: str, save_path:str, md5_hash:Optional[str]=None, max_try:int=5):
    file_dir = os.path.dirname(os.path.abspath(save_path))
    os.makedirs(file_dir, exist_ok=True)

    if not os.path.isfile(save_path) or (
        md5_hash is not None and file_md5(save_path) != md5_hash.lower()):
    
        # Try at least once
        print(f"\033[1;34mdownloading\033[0m: {url} ...")
        suc = download_file(url, save_path)
        max_try -= 1

        while not suc and max_try > 0:
            suc = download_file(url, save_path)
            max_try -= 1

        if not suc:
            print(f"\033[1;31mdownload failed\033[0m: max try exceeded")

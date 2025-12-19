# remote_auto_fetch
Fetch something from url if not exists.

GitHub repo: [https://github.com/GGN-2015/remote_auto_fetch](https://github.com/GGN-2015/remote_auto_fetch)

## Installation

```bash
pip install remote-auto-fetch
```

## Usage

```python
from remote_auto_fetch import remote_auto_fetch

# if file at save_path does not exists, download it from url (max_try = 5)
remote_auto_fetch(url, save_path)

# if file at save_path does not exists or has a different md5_hash, download it from url (max_try = 5)
# the upper or lowercase of md5_hash does not matter
remote_auto_fetch(url, save_path, md5_hash)

# change max_try
remote_auto_fetch(url, save_path, max_try=1)
```

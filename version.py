from pathlib import Path
import requests

__version__ = None  # immer global definieren!

def get_latest_release_version():
    api_url = "https://api.github.com/repos/Interleace/shptls/releases/latest"
    try:
        r = requests.get(api_url, timeout=5)
        r.raise_for_status()
        data = r.json()
        return data.get("tag_name")
    except Exception as e:
        print(f"Fehler beim Laden der Release-Version von GitHub: {e}")
        return None

my_file = Path("version.txt")

if my_file.is_file():
    try:
        with open(my_file) as f:
            __version__ = f.read().strip()
    except Exception as e:
        print(f"Fehler beim Lesen von version.txt: {e}")
else:
    __version__ = get_latest_release_version()

if not __version__:
    __version__ = "0.0.0"  # Fallback-Version

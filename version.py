from pathlib import Path
import requests

VERSION_FILE = Path("version.txt")

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

def read_local_version():
    if VERSION_FILE.is_file():
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    return None

def write_local_version(version):
    with open(VERSION_FILE, "w") as f:
        f.write(version)

def get_current_version():
    local_version = read_local_version()
    if local_version:
        return local_version
    latest = get_latest_release_version()
    if latest:
        write_local_version(latest)
        return latest
    return "0.0.0"  # fallback

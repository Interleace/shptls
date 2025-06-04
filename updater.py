import os
import sys
import requests
import subprocess
import time
from pathlib import Path
from version import get_latest_release_version, read_local_version, write_local_version

REPO_OWNER = "Interleace"
REPO_NAME = "shptls"

def download_latest_release_asset(dest_path):
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    try:
        r = requests.get(api_url, timeout=10)
        r.raise_for_status()
        release = r.json()
        assets = release.get("assets", [])
        for asset in assets:
            if asset["name"].endswith(".exe"):
                download_url = asset["browser_download_url"]
                print(f"Downloading {asset['name']} ...")
                resp = requests.get(download_url, stream=True)
                resp.raise_for_status()
                with open(dest_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                print("Download abgeschlossen.")
                return True
        print("Kein passendes EXE-Asset gefunden.")
        return False
    except Exception as e:
        print(f"Fehler beim Herunterladen der neuesten Version: {e}")
        return False

def prompt_for_update(new_version):
    answer = input(f"Neue Version {new_version} verfügbar. Möchten Sie aktualisieren? (j/N): ").strip().lower()
    return answer == "j"

def restart_program():
    print("Programm wird neu gestartet...")
    python = sys.executable
    os.execv(python, [python] + sys.argv)

def check_and_update():
    local_version = read_local_version()
    latest_version = get_latest_release_version()
    if not latest_version:
        print("Keine aktuelle Release-Version gefunden.")
        return

    if local_version != latest_version:
        print(f"Aktuelle Version: {local_version} | Neueste Version: {latest_version}")
        if prompt_for_update(latest_version):
            exe_path = Path(sys.argv[0]).resolve()
            print(f"Alte Datei: {exe_path}")
            if download_latest_release_asset(exe_path):
                write_local_version(latest_version)
                time.sleep(1)  # kurz warten, damit Datei geschrieben wird
                restart_program()
        else:
            print("Update abgebrochen.")
    else:
        print(f"Du verwendest die neueste Version: {local_version}")

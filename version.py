import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
import requests

VERSION_FILE = Path("version.txt")
REPO = "Interleace/shptls"
GITHUB_RELEASE_API = f"https://api.github.com/repos/{REPO}/releases/latest"
GITHUB_RELEASE_DOWNLOAD = f"https://github.com/{REPO}/releases/latest/download"

def get_current_version() -> str:
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text().strip()
    return get_latest_release_version() or "0.0.0"

def get_latest_release_version() -> str | None:
    try:
        r = requests.get(GITHUB_RELEASE_API, timeout=5)
        r.raise_for_status()
        return r.json().get("tag_name", "").strip()
    except Exception as e:
        print(f"Fehler beim Laden der neuesten Release-Version: {e}")
        return None

def check_for_update_and_handle(current_version: str):
    latest = get_latest_release_version()
    if not latest or latest == current_version:
        return

    print(f"Neue Version {latest} verfügbar (aktuell: {current_version})")
    confirm = input("Möchten Sie aktualisieren? (j/N): ").strip().lower()
    if confirm != "j":
        return

    if platform.system() == "Windows":
        update_windows(latest)
    else:
        print("Automatisches Update ist nur unter Windows implementiert.")
        print(f"Aktualisiere manuell von: {GITHUB_RELEASE_DOWNLOAD}/<DATEINAME>.exe")

def update_windows(latest_version: str):
    exe_name = f"shptls-{latest_version}.exe"
    url = f"{GITHUB_RELEASE_DOWNLOAD}/{exe_name}"
    print(f"Downloading {exe_name} ...")

    try:
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(exe_name, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download abgeschlossen.")

        old_path = Path(sys.argv[0])
        print(f"Ersetze {old_path} durch {exe_name} ...")

        os.remove(old_path)
        shutil.move(exe_name, old_path)

        print("Programm wird neu gestartet...")
        subprocess.Popen([str(old_path)])
        sys.exit(0)
    except Exception as e:
        print(f"Update fehlgeschlagen: {e}")

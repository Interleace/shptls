import sys
import platform
import subprocess
import os
import shutil
import requests
from pathlib import Path
import time

REPO_OWNER = "Interleace"
REPO_NAME = "shptls"
GITHUB_API_LATEST_RELEASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

def get_latest_release_tag():
    try:
        r = requests.get(GITHUB_API_LATEST_RELEASE, timeout=5)
        r.raise_for_status()
        data = r.json()
        return data.get("tag_name")
    except Exception as e:
        print(f"Fehler beim Laden der Release-Version von GitHub: {e}")
        return None

def is_frozen():
    return getattr(sys, "frozen", False)

def get_executable_path():
    if is_frozen():
        return Path(sys.executable).resolve()
    return None

def update_windows(new_version_tag):
    exe_path = get_executable_path()
    if not exe_path or not exe_path.exists():
        print("Fehler: Ausführbare Datei nicht gefunden, Update abgebrochen.")
        return False

    url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/download/{new_version_tag}/{REPO_NAME}-{new_version_tag}.exe"
    tmp_path = exe_path.parent / f"{REPO_NAME}-new.exe"

    print(f"Downloading {url} ...")
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(tmp_path, "wb") as f:
                shutil.copyfileobj(r.raw, f)
        print("Download abgeschlossen.")
    except Exception as e:
        print(f"Fehler beim Herunterladen: {e}")
        return False

    # Backup alte exe (optional)
    backup_path = exe_path.with_suffix(".old.exe")
    try:
        exe_path.rename(backup_path)
        tmp_path.rename(exe_path)
        print("Update erfolgreich. Starte neu...")
        # Neustart
        os.execv(str(exe_path), sys.argv)
    except Exception as e:
        print(f"Fehler beim Ersetzen der Datei: {e}")
        # Versuche Backup zurückzusetzen
        if backup_path.exists():
            backup_path.rename(exe_path)
        return False

def update_linux(new_version_tag):
    # Beispiel: git pull (nur wenn Repo vorhanden)
    repo_root = Path(__file__).parent.resolve()
    if (repo_root / ".git").exists():
        print("Aktualisiere via 'git pull' ...")
        try:
            result = subprocess.run(["git", "pull"], cwd=str(repo_root))
            if result.returncode == 0:
                print("Update via Git erfolgreich. Programm neu starten.")
                # Neustart
                os.execv(sys.executable, [sys.executable] + sys.argv)
            else:
                print("Git pull fehlgeschlagen.")
        except Exception as e:
            print(f"Fehler beim Ausführen von git pull: {e}")
    else:
        print("Kein Git-Repo gefunden. Bitte manuell updaten.")

def main_update_check(current_version):
    latest_version = get_latest_release_tag()
    if not latest_version:
        print("Konnte neueste Version nicht ermitteln.")
        return

    print(f"Aktuelle Version: {current_version} | Neueste Version: {latest_version}")

    if latest_version == current_version:
        print("Programm ist aktuell.")
        return

    answer = input(f"Neue Version {latest_version} verfügbar. Möchten Sie aktualisieren? (j/N): ").strip().lower()
    if answer != "j":
        print("Update abgebrochen.")
        return

    system = platform.system()
    if system == "Windows":
        if not is_frozen():
            print("Update nur im EXE-Modus möglich.")
            return
        update_windows(latest_version)
    elif system == "Linux":
        update_linux(latest_version)
    else:
        print(f"Update für OS {system} nicht unterstützt.")

if __name__ == "__main__":
    # Beispiel: aktuelle Version aus version.py importieren
    try:
        from version import __version__
    except ImportError:
        __version__ = "0.0.0"

    main_update_check(__version__)

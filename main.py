import customtkinter as ctk
from main_window import MainWindow
from config import Config
from version import get_current_version
import updater

def main():
    version = get_current_version()
    print(f"Version: {version}")

    # Prüfe auf Updates und führe ggf. Update durch (neustart)
    updater.check_and_update()

    # CustomTkinter Konfiguration
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # Hauptfenster erstellen und starten
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()

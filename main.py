import customtkinter as ctk
from main_window import MainWindow
from config import Config
from version import __version__
print(f"Version: {__version__}")


def main():
    # CustomTkinter Konfiguration
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # Hauptfenster erstellen und starten
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()

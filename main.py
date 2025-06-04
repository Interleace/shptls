import customtkinter as ctk
from main_window import MainWindow
from config import Config
from version import __version__
import updater

if __name__ == "__main__":
    print(f"Version: {__version__}")

    # Vor dem Start prüfen und ggf. updaten
    updater.main_update_check(__version__)

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    app = MainWindow()
    app.mainloop()

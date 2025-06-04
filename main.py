import customtkinter as ctk
from main_window import MainWindow
from config import Config
from version import get_current_version, check_for_update_and_handle

def main():
    current_version = get_current_version()
    print(f"Aktuelle Version: {current_version}")
    check_for_update_and_handle(current_version)

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()

# Fix for main_window.py
# Apply the same logic to SettingsWindow in this file

import customtkinter as ctk
from config import Config
from woocommerce_api import WooCommerceAPI
from create_order_window import CreateOrderWindow
from history_window import HistoryWindow
import tkinter.messagebox as msgbox

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("WooCommerce Bestellverwaltung")
        self.geometry("1080x720")
        self.resizable(True, True)

        # Konfiguration laden
        self.config = Config()
        self.woo_api = None

        self.setup_ui()
        self.check_api_connection()

    def setup_ui(self):
        """Benutzeroberfläche einrichten"""
        # Haupttitel
        title_label = ctk.CTkLabel(
            self,
            text="WooCommerce Bestellverwaltung",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=30)

        # Status Label
        self.status_label = ctk.CTkLabel(
            self,
            text="Verbindungsstatus wird geprüft...",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=10)

        # Button Frame
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=30, padx=50, fill="x")

        # Erstellen Button
        self.create_button = ctk.CTkButton(
            button_frame,
            text="Bestellung Erstellen",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            command=self.open_create_window
        )
        self.create_button.pack(pady=15, padx=20, fill="x")

        # Verlauf Button
        self.history_button = ctk.CTkButton(
            button_frame,
            text="Bestellverlauf",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            command=self.open_history_window
        )
        self.history_button.pack(pady=15, padx=20, fill="x")

        # Einstellungen Button
        settings_button = ctk.CTkButton(
            button_frame,
            text="API Einstellungen",
            font=ctk.CTkFont(size=14),
            height=40,
            command=self.open_settings
        )
        settings_button.pack(pady=15, padx=20, fill="x")

        # Buttons initial deaktivieren
        self.create_button.configure(state="disabled")
        self.history_button.configure(state="disabled")

    def check_api_connection(self):
        """API Verbindung prüfen"""
        if not self.config.is_configured():
            self.status_label.configure(
                text="❌ API nicht konfiguriert - Bitte Einstellungen öffnen",
                text_color="red"
            )
            return

        try:
            self.woo_api = WooCommerceAPI(
                self.config.woo_url,
                self.config.consumer_key,
                self.config.consumer_secret
            )

            success, message = self.woo_api.test_connection()

            if success:
                self.status_label.configure(
                    text="✅ Verbindung zu WooCommerce erfolgreich",
                    text_color="green"
                )
                self.create_button.configure(state="normal")
                self.history_button.configure(state="normal")
            else:
                self.status_label.configure(
                    text=f"❌ Verbindung fehlgeschlagen: {message}",
                    text_color="red"
                )
        except Exception as e:
            self.status_label.configure(
                text=f"❌ Verbindungsfehler: {str(e)}",
                text_color="red"
            )

    def open_create_window(self):
        """Erstellungsfenster öffnen"""
        if self.woo_api:
            create_window = CreateOrderWindow(self, self.woo_api)
        else:
            msgbox.showerror("Fehler", "Keine API Verbindung verfügbar")

    def open_history_window(self):
        """Verlaufsfenster öffnen"""
        if self.woo_api:
            history_window = HistoryWindow(self, self.woo_api)
        else:
            msgbox.showerror("Fehler", "Keine API Verbindung verfügbar")

    def open_settings(self):
        """Einstellungsfenster öffnen"""
        settings_window = SettingsWindow(self, self.config, self.check_api_connection)


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, config, callback):
        super().__init__(parent)

        self.config = config
        self.callback = callback

        self.title("API Einstellungen")
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(parent)

        self.setup_ui()
        self.update_idletasks() # Ensure window is visible before setting grab
        self.grab_set()

    def setup_ui(self):
        """Einstellungs-UI einrichten"""
        # Titel
        title_label = ctk.CTkLabel(
            self,
            text="WooCommerce API Einstellungen",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=20)

        # Eingabefelder Frame
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(pady=20, padx=30, fill="both", expand=True)

        # Shop URL
        ctk.CTkLabel(input_frame, text="Shop URL:").pack(anchor="w", padx=20, pady=(20, 5))
        self.url_entry = ctk.CTkEntry(input_frame, placeholder_text="https://deinshop.de")
        self.url_entry.pack(fill="x", padx=20, pady=(0, 15))
        self.url_entry.insert(0, self.config.woo_url)

        # Consumer Key
        ctk.CTkLabel(input_frame, text="Consumer Key:").pack(anchor="w", padx=20, pady=(0, 5))
        self.key_entry = ctk.CTkEntry(input_frame, placeholder_text="ck_...")
        self.key_entry.pack(fill="x", padx=20, pady=(0, 15))
        self.key_entry.insert(0, self.config.consumer_key)

        # Consumer Secret
        ctk.CTkLabel(input_frame, text="Consumer Secret:").pack(anchor="w", padx=20, pady=(0, 5))
        self.secret_entry = ctk.CTkEntry(input_frame, placeholder_text="cs_...", show="*")
        self.secret_entry.pack(fill="x", padx=20, pady=(0, 20))
        self.secret_entry.insert(0, self.config.consumer_secret)

        # Button Frame
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=30, pady=20)

        # Speichern Button
        save_button = ctk.CTkButton(
            button_frame,
            text="Speichern & Testen",
            command=self.save_settings
        )
        save_button.pack(side="left", padx=10, pady=10)

        # Abbrechen Button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            command=self.destroy
        )
        cancel_button.pack(side="right", padx=10, pady=10)

    def save_settings(self):
        """Einstellungen speichern"""
        self.config.woo_url = self.url_entry.get().strip()
        self.config.consumer_key = self.key_entry.get().strip()
        self.config.consumer_secret = self.secret_entry.get().strip()

        if not all([self.config.woo_url, self.config.consumer_key, self.config.consumer_secret]):
            msgbox.showerror("Fehler", "Bitte alle Felder ausfüllen")
            return

        self.config.save_config()
        msgbox.showinfo("Erfolg", "Einstellungen gespeichert")

        # Callback aufrufen und Fenster schließen
        self.callback()
        self.destroy()

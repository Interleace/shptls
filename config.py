# no changes to config.py
import json
import os

class Config:
    def __init__(self):
        self.config_file = "config.json"
        self.load_config()

    def load_config(self):
        """Konfiguration laden oder mit Standardwerten erstellen"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.woo_url = config_data.get('woo_url', '')
                    self.consumer_key = config_data.get('consumer_key', '')
                    self.consumer_secret = config_data.get('consumer_secret', '')
            except:
                self._create_default_config()
        else:
            self._create_default_config()

    def _create_default_config(self):
        """Standardkonfiguration erstellen"""
        self.woo_url = ""
        self.consumer_key = ""
        self.consumer_secret = ""
        self.save_config()

    def save_config(self):
        """Konfiguration speichern"""
        config_data = {
            'woo_url': self.woo_url,
            'consumer_key': self.consumer_key,
            'consumer_secret': self.consumer_secret
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Fehler beim Speichern der Konfiguration: {e}")

    def is_configured(self):
        """Prüfen ob WooCommerce konfiguriert ist"""
        return bool(self.woo_url and self.consumer_key and self.consumer_secret)

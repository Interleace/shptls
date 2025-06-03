# Updated woocommerce_api.py
import requests
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime

class WooCommerceAPI:
    def __init__(self, url, consumer_key, consumer_secret):
        self.url = url.rstrip('/')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_url = f"{self.url}/wp-json/wc/v2"
        self.last_response_headers = {} # To store headers for pagination info

    def _make_request(self, method, endpoint, data=None, params=None):
        """HTTP Request an WooCommerce API senden"""
        url = f"{self.api_url}/{endpoint}"
        auth = HTTPBasicAuth(self.consumer_key, self.consumer_secret)
        headers = {'Content-Type': 'application/json'}

        try:
            if method == 'GET':
                response = requests.get(url, auth=auth, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, auth=auth, headers=headers, json=data, params=params)
            elif method == 'PUT':
                response = requests.put(url, auth=auth, headers=headers, json=data, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, auth=auth, headers=headers, params=params)

            response.raise_for_status()
            self.last_response_headers = response.headers # Store headers
            return response.json()
        except requests.exceptions.RequestException as e:
            if response is not None and response.status_code:
                error_detail = response.json() if response.content else {}
                code = error_detail.get('code', 'unknown_error')
                message = error_detail.get('message', str(e))
                raise Exception(f"API Fehler ({response.status_code} - {code}): {message}")
            else:
                raise Exception(f"API Fehler: {str(e)}")

    def test_connection(self):
        """Verbindung zur API testen"""
        try:
            result = self._make_request('GET', 'system_status')
            return True, "Verbindung erfolgreich"
        except Exception as e:
            return False, str(e)

    def get_products(self, **kwargs): # Use kwargs to accept params like page, per_page, search, sku
        """Produkte abrufen"""
        try:
            return self._make_request('GET', 'products', params=kwargs)
        except Exception as e:
            print(f"Fehler beim Abrufen der Produkte: {e}")
            return []

    def create_order(self, order_data):
        """Bestellung erstellen"""
        try:
            return self._make_request('POST', 'orders', order_data)
        except Exception as e:
            raise Exception(f"Fehler beim Erstellen der Bestellung: {str(e)}")

    def get_orders(self, **kwargs): # Use kwargs to accept params like page, per_page, status
        """Bestellungen abrufen"""
        try:
            return self._make_request('GET', 'orders', params=kwargs)
        except Exception as e:
            print(f"Fehler beim Abrufen der Bestellungen: {e}")
            return []

    def update_order_status(self, order_id, new_status):
        """Bestellstatus aktualisieren"""
        try:
            return self._make_request('PUT', f'orders/{order_id}', {'status': new_status})
        except Exception as e:
            raise Exception(f"Fehler beim Aktualisieren des Bestellstatus: {str(e)}")

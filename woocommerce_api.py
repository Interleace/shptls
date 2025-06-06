import requests
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime
import os
import tempfile
from jinja2 import Template

# Optionale Abhängigkeiten für die PDF-Erstellung
try:
    import pdfkit
except ImportError:
    pdfkit = None

try:
    from weasyprint import HTML
except ImportError:
    HTML = None


class WooCommerceAPI:
    """
    Eine Klasse zur Interaktion mit der WooCommerce REST-API, inklusive lokaler Rechnungserstellung.
    """
    def __init__(self, url, consumer_key, consumer_secret):
        self.url = url.rstrip('/')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_url = f"{self.url}/wp-json/wc/v2"
        self.last_response_headers = {}

    def _make_request(self, method, endpoint, data=None, params=None, full_url=None):
        """Eine zentrale Methode zum Senden von Anfragen an die API."""
        url = full_url if full_url else f"{self.api_url}/{endpoint}"
        auth = HTTPBasicAuth(self.consumer_key, self.consumer_secret)
        headers = {'Content-Type': 'application/json'}

        # Für direkte Dateidownloads (z.B. Rechnungen) keine JSON-Header senden
        if full_url:
            headers = {}

        try:
            response = requests.request(
                method,
                url,
                auth=auth,
                headers=headers,
                json=data if method in ['POST', 'PUT'] else None,
                params=params
            )
            response.raise_for_status() # Löst eine Exception bei HTTP-Fehlern (4xx oder 5xx) aus

            # Versuche JSON zurückzugeben, andernfalls das rohe Response-Objekt
            if 'application/json' in response.headers.get('Content-Type', ''):
                return response.json()
            return response

        except requests.exceptions.RequestException as e:
            # Verbesserte Fehlerbehandlung für detailliertere Meldungen
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    message = error_detail.get('message', e.response.text)
                except json.JSONDecodeError:
                    message = e.response.text
                raise Exception(f"API Fehler ({e.response.status_code}): {message}")
            raise Exception(f"Netzwerk- oder API-Fehler: {e}")

    def test_connection(self):
        """Testet die Verbindung und Authentifizierung zur API."""
        try:
            self._make_request('GET', 'system_status')
            return True, "Verbindung erfolgreich"
        except Exception as e:
            return False, str(e)

    def get_orders(self, **kwargs):
        """Ruft eine Liste von Bestellungen ab."""
        try:
            return self._make_request('GET', 'orders', params=kwargs)
        except Exception as e:
            print(f"Fehler beim Abrufen der Bestellungen: {e}")
            return []

    def update_order_status(self, order_id, new_status):
        """Aktualisiert den Status einer bestimmten Bestellung."""
        try:
            return self._make_request('PUT', f'orders/{order_id}', {'status': new_status})
        except Exception as e:
            raise Exception(f"Fehler beim Aktualisieren des Bestellstatus: {e}")

    def get_store_settings(self):
        """Ruft allgemeine Shop-Einstellungen ab, nützlich für Rechnungen."""
        try:
            general_settings = self._make_request('GET', 'settings/general')
            return {setting['id']: setting['value'] for setting in general_settings}
        except Exception as e:
            print(f"Fehler beim Abrufen der Shop-Einstellungen: {e}")
            return {}

    def create_invoice_html(self, order_data, store_settings=None):
        """
        Erstellt Rechnungs-HTML. Lädt dynamisch 'invoice_template.html', wenn vorhanden,
        andernfalls wird eine interne Vorlage verwendet.
        """
        if not store_settings:
            store_settings = self.get_store_settings()

        template_path = 'invoice_template.html'
        template_string = ''

        # Prüfen, ob eine externe, bearbeitbare Vorlage existiert
        if os.path.exists(template_path):
            print(f"DEBUG: Lade externe HTML-Vorlage von: {template_path}")
            with open(template_path, 'r', encoding='utf-8') as f:
                template_string = f.read()
        else:
            print("DEBUG: Externe Vorlage nicht gefunden. Nutze interne HTML-Vorlage.")
            # Interne HTML-Vorlage als Fallback
            # KORREKTUR: \n in <pre>-Tags durch tatsächliche Zeilenumbrüche im String ersetzt.
            template_string = """
            <!DOCTYPE html>
            <html lang="de">
            <head>
                <meta charset="UTF-8">
                <title>Rechnung #{{ order.id }}</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px; color: #333; font-size: 14px; line-height: 1.6; }
                    .container { max-width: 800px; margin: auto; }
                    .invoice-header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #eee; padding-bottom: 20px; margin-bottom: 40px; }
                    .company-info h1 { margin: 0; font-size: 24px; color: #000; }
                    .company-info p { margin: 5px 0 0 0; color: #666; }
                    .invoice-info { text-align: right; }
                    .invoice-info h2 { margin: 0; font-size: 28px; color: #000; }
                    .invoice-info p { margin: 5px 0 0 0; font-size: 14px; color: #666; }
                    .addresses { display: flex; justify-content: space-between; margin-bottom: 40px; gap: 20px; }
                    .address-box { background-color: #f9f9f9; padding: 20px; border-radius: 5px; flex-basis: 48%; }
                    .address-box h3 { margin-top: 0; border-bottom: 1px solid #ddd; padding-bottom: 10px; font-size: 16px; }
                    .items-table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
                    .items-table th { background-color: #f2f2f2; text-align: left; padding: 12px; font-weight: bold; border-bottom: 2px solid #ddd; }
                    .items-table td { padding: 12px; border-bottom: 1px solid #eee; }
                    .items-table .text-right { text-align: right; }
                    .totals { float: right; width: 40%; }
                    .totals table { width: 100%; }
                    .totals td { padding: 10px 0; }
                    .totals .text-right { text-align: right; }
                    .totals .total-row td { font-weight: bold; font-size: 1.2em; border-top: 2px solid #333; padding-top: 15px; }
                    .footer { clear: both; margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #777; }
                    .footer h4 { color: #333; }
                    .footer pre { font-family: inherit; white-space: pre-wrap; margin: 10px 0; background-color: #f9f9f9; padding: 15px; border-radius: 4px; border: 1px solid #eee; }
                    .footer b { color: #000; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="invoice-header">
                        <div class="company-info">
                            <h1>{{ store_name }}</h1>
                            <p>{{ store_address }}</p>
                        </div>
                        <div class="invoice-info">
                            <h2>RECHNUNG</h2>
                            <p>#{{ order.id }}</p>
                            <p><strong>Rechnungsdatum:</strong> {{ invoice_date }}</p>
                            <p><strong>Bestelldatum:</strong> {{ order_date }}</p>
                        </div>
                    </div>
                    <div class="addresses">
                         <div class="address-box">
                            <h3>Rechnungsadresse</h3>
                            <p>
                                <strong>{{ billing.first_name }} {{ billing.last_name }}</strong><br>
                                {% if billing.company %}{{ billing.company }}<br>{% endif %}
                                {{ billing.address_1 }}<br>
                                {% if billing.address_2 %}{{ billing.address_2 }}<br>{% endif %}
                                {{ billing.postcode }} {{ billing.city }}<br>
                                {{ billing.country }}
                            </p>
                        </div>
                        {% if shipping and (shipping.address_1 != billing.address_1 or shipping.first_name != billing.first_name) %}
                        <div class="address-box">
                            <h3>Lieferadresse</h3>
                            <p>
                                <strong>{{ shipping.first_name }} {{ shipping.last_name }}</strong><br>
                                {% if shipping.company %}{{ shipping.company }}<br>{% endif %}
                                {{ shipping.address_1 }}<br>
                                {% if shipping.address_2 %}{{ shipping.address_2 }}<br>{% endif %}
                                {{ shipping.postcode }} {{ shipping.city }}<br>
                                {{ shipping.country }}
                            </p>
                        </div>
                        {% endif %}
                    </div>
                    <table class="items-table">
                        <thead>
                            <tr><th>Artikel</th><th class="text-right">Menge</th><th class="text-right">Einzelpreis</th><th class="text-right">Gesamt</th></tr>
                        </thead>
                        <tbody>
                            {% for item in line_items %}
                            <tr><td>{{ item.name }}</td><td class="text-right">{{ item.quantity }}</td><td class="text-right">{{ "%.2f"|format(item.price|float) }} {{ currency_symbol }}</td><td class="text-right">{{ item.total }} {{ currency_symbol }}</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    <div class="totals">
                        <table>
                            <tr><td>Zwischensumme</td><td class="text-right">{{ "%.2f"|format(order.total|float - order.total_tax|float) }} {{ currency_symbol }}</td></tr>
                            {% for shipping_line in shipping_lines %}
                            <tr><td>{{ shipping_line.method_title }}</td><td class="text-right">{{ shipping_line.total }} {{ currency_symbol }}</td></tr>
                            {% endfor %}
                            {% if order.total_tax|float > 0 %}
                            <tr><td>MwSt ({{ tax_rate }}%)</td><td class="text-right">{{ order.total_tax }} {{ currency_symbol }}</td></tr>
                            {% endif %}
                            <tr class="total-row"><td>Gesamtsumme</td><td class="text-right">{{ order.total }} {{ currency_symbol }}</td></tr>
                        </table>
                    </div>
                    <div class="footer">
                        <p><strong>Zahlungsweise:</strong> {{ order.payment_method_title }}</p>
                        {% if order.customer_note %}<p><strong>Kundennotiz:</strong> {{ order.customer_note }}</p>{% endif %}
                        <hr>
                        <h4>Schlussformel: Kauf auf Rechnung</h4>
                        <p>Bezahlen Sie nach Erhalt der Lieferung hier mit Kreditkarte, Überweisung oder PayPal: <a href="https://bit.ly/Buchrechnung">https://bit.ly/Buchrechnung</a></p>
                        <p>PayPal-Zahlungen können auch direkt gesendet werden an: <a href="https://www.paypal.com/paypalme/ARIBildung">https://www.paypal.com/paypalme/ARIBildung</a></p>
                        <p>oder überweisen Sie den Rechnungsbetrag an unsere unten aufgeführte Bankverbindung:</p>
                        <pre><b>Kontoinhaber</b>: ARI-Bildungseinrichtung e.V.
<b>IBAN</b>: DE33 1004 0000 0893 2212 00
<b>BIC</b>: COBADEFFXXX
<b>Bank</b>: Commerzbank Berlin
<<p>Rechnungs-Nr.: #{{ order.id }}</p>/pre>
                        <p><b>Geben Sie bitte immer die Rechnungsnummer als Betreff an!</b></p>
                        <p>Vielen Dank für Ihre Bestellung,<br>Ihr Kabbalabuch Service Team</p>
                        <hr>
                        <pre><b>geschäftsadresse:</b>
ARI (Aschlag Research Institute) Bildungseinrichtung e.V.
Goslarsche Str. 2
38118 Braunschweig
Germany

<b>Shopowner:</b> kabbalabuch.info</pre>
                    </div>
                </div>
            </body>
            </html>
            """

        template_data = {
            'order': order_data,
            'store_name': store_settings.get('woocommerce_store_name', 'ARI Bildungseinrichtung e.V.'),
            'store_address': store_settings.get('woocommerce_store_address', 'kabbalabuch.info\nGoslarsche Str. 2\n38118 Braunschweig\nGermany'),
            'billing': order_data.get('billing', {}),
            'shipping': order_data.get('shipping', {}),
            'line_items': order_data.get('line_items', []),
            'shipping_lines': order_data.get('shipping_lines', []),
            'currency_symbol': order_data.get('currency_symbol', '€'),
            'invoice_date': datetime.now().strftime('%d.%m.%Y'),
            'order_date': self._format_date(order_data.get('date_created', '')),
            'tax_rate': 19
        }

        template = Template(template_string)
        return template.render(**template_data)

    def _format_date(self, date_string):
        """Formatiert ein ISO-Datum sicher in ein deutsches Format."""
        if not date_string: return "N/A"
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00')).strftime('%d.%m.%Y %H:%M')
        except ValueError:
            return date_string

    def create_invoice_pdf(self, order_data, save_path, store_settings=None):
        """
        Erstellt eine PDF-Rechnung aus Bestelldaten. Versucht zuerst WeasyPrint,
        dann pdfkit. Wenn beides fehlschlägt, wird eine HTML-Datei gespeichert.
        """
        try:
            html_content = self.create_invoice_html(order_data, store_settings)
            pdf_created = False

            # Methode 1: WeasyPrint (bevorzugt)
            if HTML:
                try:
                    HTML(string=html_content).write_pdf(save_path)
                    pdf_created = True
                    print(f"DEBUG: PDF erfolgreich mit WeasyPrint erstellt: {save_path}")
                except Exception as e:
                    print(f"DEBUG: WeasyPrint-Fehler: {e}")

            # Methode 2: pdfkit (Fallback)
            if not pdf_created and pdfkit:
                try:
                    pdfkit.from_string(html_content, save_path, options={'encoding': "UTF-8"})
                    pdf_created = True
                    print(f"DEBUG: PDF erfolgreich mit pdfkit erstellt: {save_path}")
                except Exception as e:
                    print(f"DEBUG: pdfkit-Fehler: {e}")

            if pdf_created:
                return True
            else:
                # Fallback: Wenn keine PDF-Bibliothek funktioniert, HTML speichern
                html_fallback_path = save_path.replace('.pdf', '.html')
                with open(html_fallback_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print("WARNUNG: Keine PDF-Bibliothek (WeasyPrint, pdfkit) funktionierte. Speichere HTML-Fallback.")
                return html_fallback_path

        except Exception as e:
            raise Exception(f"Kritischer Fehler beim Erstellen der PDF-Rechnung: {e}")

    def get_or_create_invoice(self, order_id, save_path):
        """
        Robuste Methode zur Rechnungsbeschaffung.
        1. Versucht, eine vorhandene Rechnung vom Server herunterzuladen.
        2. Wenn das fehlschlägt, wird eine neue Rechnung lokal erstellt.
        """
        print(f"DEBUG: Starte Rechnungs-Workflow für Bestellung {order_id}...")
        try:
            print("DEBUG: Schritt 1: Versuche, vorhandene Rechnung herunterzuladen...")
            result = self.download_invoice_pdf(order_id, save_path)
            if result is True:
                print("DEBUG: Download erfolgreich.")
                return True
            if isinstance(result, str) and os.path.exists(result):
                print("DEBUG: HTML-Rechnung heruntergeladen, PDF-Konvertierung fehlgeschlagen.")
                return result
        except Exception as e:
            print(f"DEBUG: Download fehlgeschlagen: {e}. Wechsle zu lokaler Erstellung.")

        print("DEBUG: Schritt 2: Erstelle neue Rechnung lokal...")
        try:
            order_data = self._make_request('GET', f'orders/{order_id}')
            if not order_data:
                raise Exception(f"Bestelldaten für ID {order_id} konnten nicht abgerufen werden.")

            return self.create_invoice_pdf(order_data, save_path)
        except Exception as e:
            raise Exception(f"Weder Download noch lokale Erstellung der Rechnung war möglich: {e}")

    def download_invoice_pdf(self, order_id, save_path):
        """
        Versucht, eine PDF-Rechnung mit verschiedenen gängigen Plugin-Methoden herunterzuladen.
        """
        download_methods = [
            {"name": "Print Invoice & Delivery Notes Plugin", "url": f"{self.url}/wp-admin/admin-ajax.php?action=print_order_document&order_id={order_id}&document_type=invoice"},
            {"name": "Generischer REST API Endpunkt", "url": f"{self.url}/wp-json/wc/v3/orders/{order_id}/invoice"}
        ]

        for method_info in download_methods:
            print(f"DEBUG: Versuche Download-Methode: {method_info['name']}")
            try:
                # Direkter Request, um volle Kontrolle über die Antwort zu haben
                response = requests.get(method_info['url'], auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret), timeout=15)
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/pdf' in content_type:
                        with open(save_path, 'wb') as f:
                            f.write(response.content)
                        return True # Erfolg!
                    elif 'text/html' in content_type and response.text.strip() not in ["0", ""]:
                        # HTML erhalten, versuche Konvertierung
                        temp_html_path = os.path.join(tempfile.gettempdir(), f"invoice_{order_id}_raw.html")
                        with open(temp_html_path, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        if pdfkit:
                            try:
                                pdfkit.from_file(temp_html_path, save_path)
                                os.remove(temp_html_path)
                                return True # Erfolg nach Konvertierung!
                            except Exception:
                                return temp_html_path # Konvertierung fehlgeschlagen, gib HTML zurück
                        return temp_html_path # pdfkit nicht da, gib HTML zurück
            except requests.exceptions.RequestException as e:
                print(f"DEBUG: Fehler bei Methode '{method_info['name']}': {e}")
                continue # Nächste Methode versuchen

        raise Exception("Keine der Download-Methoden war erfolgreich.")

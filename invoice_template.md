# Rechnung #{{ order.id }}

| Firmendaten | Rechnungsinformationen |
| :--- | :--- |
| **{{ store_name }}** | **Rechnungsdatum:** {{ invoice_date }} |
| {{ store_address }} | **Bestelldatum:** {{ order_date }} |
| {% if store_phone %}Tel: {{ store_phone }}{% endif %} | **Status:** {{ order.status }} |
| {% if store_email %}E-Mail: {{ store_email }}{% endif %} | |

---

ARI (Aschlag Research Institute) Bildungseinrichtung e.V.

Goslarsche Str. 2
38118 Braunschweig
Germany

### Rechnungsadresse

**{{ billing.first_name }} {{ billing.last_name }}**
{% if billing.company %}{{ billing.company }}{% endif %}
{{ billing.address_1 }}{% if billing.address_2 %}, {{ billing.address_2 }}{% endif %}
{{ billing.postcode }} {{ billing.city }}
{{ billing.country }}

**E-Mail:** {{ billing.email }}
**Telefon:** {{ billing.phone }}

---

{% if shipping and (shipping.address_1 != billing.address_1 or shipping.first_name != billing.first_name) %}
### Lieferadresse

**{{ shipping.first_name }} {{ shipping.last_name }}**
{% if shipping.company %}{{ shipping.company }}{% endif %}
{{ shipping.address_1 }}{% if shipping.address_2 %}, {{ shipping.address_2 }}{% endif %}
{{ shipping.postcode }} {{ shipping.city }}
{{ shipping.country }}

---
{% endif %}

### Bestellte Artikel

| Artikel | Menge | Einzelpreis | Gesamtpreis |
| :--- | :--- | :--- | :--- |
{% for item in line_items %}| {{ item.name }} | {{ item.quantity }} | {{ "%.2f"|format(item.price|float) }} {{ currency_symbol }} | {{ item.total }} {{ currency_symbol }} |
{% endfor %}

---

**Zwischensumme:** {{ order.total|float - order.total_tax|float }} {{ currency_symbol }}
{% for shipping_line in shipping_lines %}
**{{ shipping_line.method_title }}:** {{ shipping_line.total }} {{ currency_symbol }}
{% endfor %}
{% if order.total_tax|float > 0 %}
**MwSt ({{ tax_rate }}%):** {{ order.total_tax }} {{ currency_symbol }}
{% endif %}
### **Gesamtsumme: {{ order.total }} {{ currency_symbol }}**

---

**Zahlungsweise:** {{ order.payment_method_title }}
{% if order.customer_note %}
**Kundennotiz:** {{ order.customer_note }}
{% endif %}

---

#### Kauf auf Rechnung
Bezahlen Sie nach Erhalt der Lieferung hier mit Kreditkarte, Überweisung oder PayPal: https://bit.ly/Buchrechnung

PayPal-Zahlungen können auch direkt gesendet werden an:
https://www.paypal.com/paypalme/ARIBildung

oder überweisen Sie den Rechnungsbetrag an unsere unten aufgeführte Bankverbindung:

**Kontoinhaber**: ARI-Bildungseinrichtung e.V.
**IBAN**: DE33 1004 0000 0893 2212 00
**BIC**: COBADEFFXXX
**Bank**: Commerzbank Berlin

**Geben Sie bitte immer die Rechnungsnummer als Betreff an!**

Vielen Dank für Ihre Bestellung,
Ihr Kabbalabuch Service Team

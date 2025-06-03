# create_order_window.py
import customtkinter as ctk
import tkinter.messagebox as msgbox
from datetime import datetime
from tkinter import ttk
import threading
# Import ProductSearchDialog (assuming it's in a separate file as discussed)
from product_search_dialog import ProductSearchDialog


# Neuer Dialog für die Bestätigung zum Fortfahren bei fehlenden Feldern
class ConfirmProceedDialog(ctk.CTkToplevel):
    def __init__(self, parent, message):
        super().__init__(parent)
        self.result = False # Standardmäßig nicht fortfahren

        self.title("Warnung: Unvollständige Felder")
        self.geometry("450x250")
        self.resizable(False, False)
        self.transient(parent)

        # Fix: Hauptframe für den Inhalt des Dialogs - Muss fill und expand haben
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main_frame, text=message, wraplength=400, justify="left", font=ctk.CTkFont(size=14)).pack(pady=(0, 20), padx=5)

        button_frame = ctk.CTkFrame(main_frame) # Muss im main_frame gepackt werden
        button_frame.pack(pady=10) # Kein fill/expand hier, da es nur Buttons enthält und zentriert sein soll

        # Button zum Abbrechen/Zurückkehren
        ok_button = ctk.CTkButton(button_frame, text="OK (Zurück)", command=self.ok_clicked)
        ok_button.pack(side="left", padx=10)

        # Button zum Fortfahren
        weiter_button = ctk.CTkButton(button_frame, text="Weiter (Trotzdem bestellen)", command=self.weiter_clicked)
        weiter_button.pack(side="right", padx=10)

        self.update_idletasks() # Ensure window is visible before setting grab
        self.after(1, self.grab_set) # Use after to ensure window is mapped
        self.focus_force() # Ensure focus is on the dialog


    def ok_clicked(self):
        """Der Benutzer möchte die Eingaben korrigieren."""
        self.result = False
        self.destroy()

    def weiter_clicked(self):
        """Der Benutzer möchte trotz fehlender Felder fortfahren."""
        self.result = True
        self.destroy()


class CreateOrderWindow(ctk.CTkToplevel):
    def __init__(self, parent, woo_api):
        super().__init__(parent)

        self.woo_api = woo_api
        self.selected_products = [] # List to hold dictionaries of selected products

        self.title("Neue Bestellung erstellen")
        self.geometry("900x800")
        self.resizable(True, True)
        self.transient(parent)

        self.setup_ui()
        self.update_idletasks() # Ensure window is visible before setting grab
        self.after(1, self.grab_set) # Use after to ensure window is mapped
        self.focus_force() # Ensure focus is on the dialog


    def setup_ui(self):
        """UI einrichten"""
        # Scrollbares Hauptframe
        main_scroll = ctk.CTkScrollableFrame(self)
        main_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Titel
        title_label = ctk.CTkLabel(
            main_scroll,
            text="Neue Bestellung erstellen",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # Allgemeine Details
        self.setup_general_details(main_scroll)

        # Rechnungsdetails
        self.setup_billing_details(main_scroll)

        # Produkte (updated to use the search dialog)
        self.setup_products_section(main_scroll)

        # Bestellung abschicken
        self.setup_submit_section(main_scroll)

    def setup_general_details(self, parent):
        """Allgemeine Details Sektion"""
        general_frame = ctk.CTkFrame(parent)
        general_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            general_frame,
            text="Allgemeine Details",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        # Grid für Eingabefelder
        details_grid = ctk.CTkFrame(general_frame)
        details_grid.pack(fill="x", padx=20, pady=(0, 20))

        # Bestelldatum
        ctk.CTkLabel(details_grid, text="Bestelldatum:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.order_date = ctk.CTkEntry(details_grid)
        self.order_date.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        self.order_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Bestellstatus
        ctk.CTkLabel(details_grid, text="Status:").grid(row=0, column=2, sticky="w", padx=10, pady=5)
        self.order_status = ctk.CTkComboBox(
            details_grid,
            values=["pending", "processing", "on-hold", "completed", "cancelled", "refunded", "failed"]
        )
        self.order_status.grid(row=0, column=3, sticky="ew", padx=10, pady=5)
        self.order_status.set("pending")

        # Kunde
        ctk.CTkLabel(details_grid, text="Kunde:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.customer = ctk.CTkEntry(details_grid, placeholder_text="Gast")
        self.customer.grid(row=1, column=1, columnspan=3, sticky="ew", padx=10, pady=5)
        self.customer.insert(0, "Gast")

        # Grid konfigurieren
        details_grid.grid_columnconfigure(1, weight=1)
        details_grid.grid_columnconfigure(3, weight=1)

    def setup_billing_details(self, parent):
        """Rechnungsdetails Sektion"""
        billing_frame = ctk.CTkFrame(parent)
        billing_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            billing_frame,
            text="Rechnungsdetails",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        # Grid für Rechnungsfelder
        billing_grid = ctk.CTkFrame(billing_frame)
        billing_grid.pack(fill="x", padx=20, pady=(0, 20))

        # Erste Zeile: Vorname, Nachname
        ctk.CTkLabel(billing_grid, text="Vorname:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.first_name = ctk.CTkEntry(billing_grid)
        self.first_name.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(billing_grid, text="Nachname:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.last_name = ctk.CTkEntry(billing_grid)
        self.last_name.grid(row=0, column=3, sticky="ew", padx=5, pady=5)

        # Zweite Zeile: Firma, Email
        ctk.CTkLabel(billing_grid, text="Firma:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.company = ctk.CTkEntry(billing_grid)
        self.company.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(billing_grid, text="Email:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.email = ctk.CTkEntry(billing_grid)
        self.email.grid(row=1, column=3, sticky="ew", padx=5, pady=5)

        # Dritte Zeile: Adresse 1, Adresse 2
        ctk.CTkLabel(billing_grid, text="Adresse 1:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.address_1 = ctk.CTkEntry(billing_grid)
        self.address_1.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(billing_grid, text="Adresse 2:").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        self.address_2 = ctk.CTkEntry(billing_grid)
        self.address_2.grid(row=2, column=3, sticky="ew", padx=5, pady=5)

        # Vierte Zeile: PLZ, Stadt
        ctk.CTkLabel(billing_grid, text="PLZ:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.postcode = ctk.CTkEntry(billing_grid)
        self.postcode.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(billing_grid, text="Stadt:").grid(row=3, column=2, sticky="w", padx=5, pady=5)
        self.city = ctk.CTkEntry(billing_grid)
        self.city.grid(row=3, column=3, sticky="ew", padx=5, pady=5)

        # Fünfte Zeile: Bundesland, Land
        ctk.CTkLabel(billing_grid, text="Bundesland:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.state = ctk.CTkEntry(billing_grid)
        self.state.grid(row=4, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(billing_grid, text="Land:").grid(row=4, column=2, sticky="w", padx=5, pady=5)
        self.country = ctk.CTkEntry(billing_grid)
        self.country.grid(row=4, column=3, sticky="ew", padx=5, pady=5)
        self.country.insert(0, "DE")

        # Sechste Zeile: Telefon, Zahlungsart
        ctk.CTkLabel(billing_grid, text="Telefon:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.phone = ctk.CTkEntry(billing_grid)
        self.phone.grid(row=5, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(billing_grid, text="Zahlungsart:").grid(row=5, column=2, sticky="w", padx=5, pady=5)
        self.payment_method = ctk.CTkComboBox(
            billing_grid,
            values=["bacs", "cheque", "cod", "paypal", "stripe"]
        )
        self.payment_method.grid(row=5, column=3, sticky="ew", padx=5, pady=5)
        self.payment_method.set("bacs")

        # Siebte Zeile: Transaktions-ID
        ctk.CTkLabel(billing_grid, text="Transaktions-ID:").grid(row=6, column=0, sticky="w", padx=5, pady=5)
        self.transaction_id = ctk.CTkEntry(billing_grid)
        self.transaction_id.grid(row=6, column=1, columnspan=3, sticky="ew", padx=5, pady=5)

        # Grid konfigurieren
        for i in range(4):
            billing_grid.grid_columnconfigure(i, weight=1)

    def setup_products_section(self, parent):
        """Produkte Sektion (aktualisiert für Produkt-Suchdialog)"""
        products_frame = ctk.CTkFrame(parent)
        products_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            products_frame,
            text="Produkte",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        # Button zum Öffnen des Produkt-Suchdialogs
        open_search_button = ctk.CTkButton(
            products_frame,
            text="Produkte suchen und hinzufügen",
            command=self.open_product_search_dialog
        )
        open_search_button.pack(padx=20, pady=(0, 10), anchor="e")

        # Ausgewählte Produkte Liste (jetzt ein Treeview)
        self.products_tree = ttk.Treeview(
            products_frame,
            columns=("ID", "Name", "SKU", "Menge", "Preis", "Summe"),
            show="headings"
        )
        self.products_tree.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.products_tree.heading("ID", text="ID")
        self.products_tree.heading("Name", text="Name")
        self.products_tree.heading("SKU", text="SKU")
        self.products_tree.heading("Menge", text="Menge")
        self.products_tree.heading("Preis", text="Einzelpreis (€)")
        self.products_tree.heading("Summe", text="Gesamtsumme (€)")

        self.products_tree.column("ID", width=50, stretch=False)
        self.products_tree.column("Name", width=200, stretch=True)
        self.products_tree.column("SKU", width=100, stretch=False)
        self.products_tree.column("Menge", width=70, stretch=False, anchor="center")
        self.products_tree.column("Preis", width=90, stretch=False, anchor="e")
        self.products_tree.column("Summe", width=100, stretch=False, anchor="e")

        # Context menu for selected products
        self.products_tree.bind("<Button-3>", self.show_selected_product_context_menu)


        # Total Price Label
        self.total_price_label = ctk.CTkLabel(
            products_frame,
            text="Gesamtsumme: 0.00 €",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.total_price_label.pack(anchor="e", padx=20, pady=10)

        # Rabatt und MwSt (keeping these for existing functionality)
        extras_frame = ctk.CTkFrame(products_frame)
        extras_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(extras_frame, text="Rabatt (%):").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.discount_entry = ctk.CTkEntry(extras_frame, width=100)
        self.discount_entry.grid(row=0, column=1, padx=10, pady=10)
        self.discount_entry.insert(0, "0")

        ctk.CTkLabel(extras_frame, text="Versandkosten:").grid(row=0, column=2, sticky="w", padx=10, pady=10)
        self.shipping_entry = ctk.CTkEntry(extras_frame, width=100)
        self.shipping_entry.grid(row=0, column=3, padx=10, pady=10)
        self.shipping_entry.insert(0, "0")

        ctk.CTkLabel(extras_frame, text="MwSt (%):").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.tax_entry = ctk.CTkEntry(extras_frame, width=100) # This field is for display/info, not directly sent to WC API for tax override in this version
        self.tax_entry.grid(row=1, column=1, padx=10, pady=10)
        self.tax_entry.insert(0, "19") # Default display value

    def setup_submit_section(self, parent):
        """Submit Sektion"""
        submit_frame = ctk.CTkFrame(parent)
        submit_frame.pack(fill="x", pady=(0, 20))

        button_frame = ctk.CTkFrame(submit_frame)
        button_frame.pack(pady=20)

        # Bestellung erstellen Button
        create_button = ctk.CTkButton(
            button_frame,
            text="Bestellung erstellen",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40,
            width=200,
            command=self.create_order
        )
        create_button.pack(side="left", padx=10)

        # Abbrechen Button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            height=40,
            width=100,
            command=self.destroy
        )
        cancel_button.pack(side="left", padx=10)


    def open_product_search_dialog(self):
        """Öffnet den Produkt-Suchdialog und verarbeitet die Ergebnisse"""
        dialog = ProductSearchDialog(self, self.woo_api) # Pass woo_api here
        self.wait_window(dialog) # Wait until the dialog is closed

        if dialog.result: # dialog.result will contain a list of selected product dictionaries
            for product_data in dialog.result:
                # Add default quantity of 1 if not already set by dialog
                if 'quantity' not in product_data:
                    product_data['quantity'] = 1

                self.selected_products.append(product_data)
            self.update_selected_products_treeview() # Update the display in CreateOrderWindow

    def update_selected_products_treeview(self):
        """Aktualisiert die Treeview der ausgewählten Produkte"""
        # Clear existing items in the treeview
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        total_order_price = 0.0
        for product in self.selected_products:
            # Ensure price and quantity are numeric before calculation
            try:
                price = float(product.get('price', 0.0))
            except (ValueError, TypeError):
                price = 0.0
                print(f"Warning: Non-numeric price for product '{product.get('name', 'N/A')}'. Using 0.0.")

            try:
                quantity = int(product.get('quantity', 0))
            except (ValueError, TypeError):
                quantity = 0
                print(f"Warning: Non-numeric quantity for product '{product.get('name', 'N/A')}'. Using 0.")

            item_total_price = quantity * price
            total_order_price += item_total_price

            # Insert into Treeview
            self.products_tree.insert(
                "", "end",
                values=(
                    product.get('id', 'N/A'), # ID for WooCommerce products, 'N/A' for custom
                    product.get('name', 'Unbekanntes Produkt'),
                    product.get('sku', 'N/A'),
                    quantity,
                    f"{price:.2f}",
                    f"{item_total_price:.2f}"
                ),
                # Store the product dictionary with the item for easy retrieval during edit/remove
                tags=(f"product_{product.get('id', 'custom')}",) # Use product ID or 'custom' as tag
            )
        self.total_price_label.configure(text=f"Gesamtsumme: {total_order_price:.2f} €")

    def show_selected_product_context_menu(self, event):
        """Zeigt ein Kontextmenü für ausgewählte Produkte in der Treeview an"""
        item_id = self.products_tree.identify_row(event.y)
        if not item_id:
            return

        self.products_tree.selection_set(item_id) # Select the clicked item
        menu = ctk.CTkContextMenu(self, fg_color="#333333", bg_color="#222222") # Using CTkContextMenu if available, else fallback
        menu.add_command(label="Bearbeiten", command=self.edit_selected_product)
        menu.add_command(label="Entfernen", command=self.remove_selected_product)
        menu.tk_popup(event.x_root, event.y_root)


    def edit_selected_product(self):
        """Bearbeitet ein ausgewähltes Produkt in der Treeview"""
        selected_item_id = self.products_tree.selection()
        if not selected_item_id:
            msgbox.showinfo("Info", "Bitte ein Produkt zum Bearbeiten auswählen.")
            return

        # Get the index of the selected item in the treeview
        index = self.products_tree.index(selected_item_id[0])
        product_to_edit = self.selected_products[index]

        dialog = EditProductDialog(self, product_to_edit)
        self.wait_window(dialog)

        if dialog.result:
            # Update the product in the selected_products list with the dialog's result
            for key, value in dialog.result.items():
                product_to_edit[key] = value
            self.update_selected_products_treeview() # Re-render the treeview

    def remove_selected_product(self):
        """Entfernt ein ausgewähltes Produkt aus der Treeview und Liste"""
        selected_item_id = self.products_tree.selection()
        if not selected_item_id:
            msgbox.showinfo("Info", "Bitte ein Produkt zum Entfernen auswählen.")
            return

        if msgbox.askyesno("Bestätigen", "Möchten Sie das ausgewählte Produkt wirklich entfernen?"):
            index = self.products_tree.index(selected_item_id[0])
            del self.selected_products[index]
            self.update_selected_products_treeview() # Re-render the treeview

    def create_order(self):
        """Bestellung bei WooCommerce erstellen"""
        if not self.selected_products:
            msgbox.showerror("Fehler", "Bitte mindestens ein Produkt hinzufügen")
            return

        missing_fields = []
        # Überprüfung der erforderlichen Rechnungsdetails
        if not self.first_name.get().strip(): missing_fields.append("Vorname")
        if not self.last_name.get().strip(): missing_fields.append("Nachname")
        if not self.email.get().strip(): missing_fields.append("Email")
        if not self.address_1.get().strip(): missing_fields.append("Adresse 1")
        if not self.city.get().strip(): missing_fields.append("Stadt")
        if not self.postcode.get().strip(): missing_fields.append("PLZ")
        if not self.country.get().strip(): missing_fields.append("Land")

        if missing_fields:
            warning_message = "Folgende erforderliche Felder sind nicht ausgefüllt:\n\n" + \
                              ", ".join(missing_fields) + \
                              "\n\nMöchten Sie die Bestellung trotzdem abschicken?"
            dialog = ConfirmProceedDialog(self, warning_message)
            self.wait_window(dialog)
            if not dialog.result:
                return

        try:
            order_data = {
                'status': self.order_status.get(),
                'customer_note': f"Erstellt mit WooCommerce Bestellverwaltung am {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                'billing': {
                    'first_name': self.first_name.get(), 'last_name': self.last_name.get(),
                    'company': self.company.get(), 'address_1': self.address_1.get(),
                    'address_2': self.address_2.get(), 'city': self.city.get(),
                    'state': self.state.get(), 'postcode': self.postcode.get(),
                    'country': self.country.get(), 'email': self.email.get(),
                    'phone': self.phone.get()
                },
                'shipping': {
                    'first_name': self.first_name.get(), 'last_name': self.last_name.get(),
                    'company': self.company.get(), 'address_1': self.address_1.get(),
                    'address_2': self.address_2.get(), 'city': self.city.get(),
                    'state': self.state.get(), 'postcode': self.postcode.get(),
                    'country': self.country.get()
                },
                'line_items': [],
                'payment_method': self.payment_method.get(),
                'payment_method_title': self.payment_method.get().replace('_', ' ').title(),
                'transaction_id': self.transaction_id.get(),
                'fee_lines': [], # Initialize for potential discount
                'shipping_lines': [] # Initialize for potential shipping
            }

            # Produkte hinzufügen und Subtotal für Rabatt berechnen
            products_subtotal = 0.0
            for selected_product_data in self.selected_products:
                line_item = {}
                try:
                    quantity = int(selected_product_data.get('quantity', 1))
                    line_item['quantity'] = quantity
                except (ValueError, TypeError):
                    line_item['quantity'] = 1 # Default to 1 if invalid

                current_product_price = 0.0
                try:
                    current_product_price = float(selected_product_data.get('price', 0.0))
                except (ValueError, TypeError):
                    current_product_price = 0.0
                    print(f"Warning: Invalid price for product {selected_product_data.get('name')} during order creation.")

                products_subtotal += current_product_price * line_item['quantity']

                if selected_product_data.get('id') and not selected_product_data.get('is_custom_product', False):
                    line_item['product_id'] = selected_product_data['id']
                    # For existing products, price is usually determined by WC from product ID.
                    # If you need to send a specific price for an existing product (e.g. a sale price not yet in WC),
                    # you might need to add 'price': str(current_product_price) to line_item,
                    # but this depends on WC API version and settings (if it allows overriding catalog price this way).
                    # Typically, 'total' and 'subtotal' are calculated by WC.
                else:
                    line_item['name'] = selected_product_data.get('name', 'Benutzerdefiniertes Produkt')
                    line_item['price'] = str(current_product_price) # Unit price for custom item

                order_data['line_items'].append(line_item)

            # Rabatt hinzufügen (als Fee Line)
            discount_percent_str = self.discount_entry.get().strip() or "0"
            discount_percent = 0.0
            try:
                discount_percent = float(discount_percent_str)
                if not (0 <= discount_percent <= 100): # Percentage should be between 0 and 100
                    msgbox.showwarning("Warnung", "Rabattprozentsatz muss zwischen 0 und 100 liegen. Wird ignoriert.")
                    discount_percent = 0.0
            except ValueError:
                msgbox.showwarning("Warnung", "Ungültiger Rabattprozentsatz. Wird ignoriert.")
                discount_percent = 0.0

            if discount_percent > 0 and products_subtotal > 0:
                discount_amount = (products_subtotal * discount_percent) / 100.0
                order_data['fee_lines'].append({
                    'name': f'Manueller Rabatt ({discount_percent:.2f}%)',
                    'total': f"{-discount_amount:.2f}", # Negative value for discount
                    'tax_status': 'taxable',  # This fee (discount) will be considered in tax calculations
                    'tax_class': ''           # Use default tax class
                })

            # Versandkosten hinzufügen
            shipping_cost_str = self.shipping_entry.get().strip() or "0"
            shipping_cost = 0.0
            try:
                shipping_cost = float(shipping_cost_str)
                if shipping_cost < 0:
                    msgbox.showwarning("Warnung", "Versandkosten dürfen nicht negativ sein. Werden auf 0.0 gesetzt.")
                    shipping_cost = 0.0
            except ValueError:
                msgbox.showwarning("Warnung", "Ungültige Versandkosten. Werden auf 0.0 gesetzt.")
                shipping_cost = 0.0

            if shipping_cost > 0:
                order_data['shipping_lines'].append({
                    'method_id': 'flat_rate',
                    'method_title': 'Pauschalversand',
                    'total': f"{shipping_cost:.2f}"
                })

            # Clean up empty fee_lines or shipping_lines if not used
            if not order_data['fee_lines']:
                del order_data['fee_lines']
            if not order_data['shipping_lines']:
                del order_data['shipping_lines']

            threading.Thread(target=self._create_order_thread, args=(order_data,), daemon=True).start()

        except ValueError as e:
            msgbox.showerror("Fehler", f"Ungültige Eingabe in numerischen Feldern: {e}")
        except Exception as e:
            msgbox.showerror("Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {e}")


    def _create_order_thread(self, order_data):
        """Threaded function to create the order via WooCommerce API"""
        try:
            # Show an "in progress" message immediately
            self.after(0, lambda: self.master.status_label.configure(text="Bestellung wird erstellt...", text_color="blue") if hasattr(self.master, 'status_label') else None) # Assuming master is MainWindow with status_label
            self.after(0, lambda: msgbox.showinfo("Info", "Bestellung wird erstellt...", parent=self)) # Show info to user on current window

            response = self.woo_api.create_order(order_data)

            if response and 'id' in response:
                success_msg = f"Bestellung #{response['id']} erfolgreich erstellt!"
                self.after(0, lambda: msgbox.showinfo("Erfolg", success_msg, parent=self))
                self.after(0, lambda: self.master.status_label.configure(text=success_msg, text_color="green") if hasattr(self.master, 'status_label') else None)
                self.after(0, self.destroy)
            else:
                error_msg = f"Bestellung konnte nicht erstellt werden. API-Antwort: {response}"
                self.after(0, lambda: msgbox.showerror("Fehler", error_msg, parent=self))
                self.after(0, lambda: self.master.status_label.configure(text=error_msg, text_color="red") if hasattr(self.master, 'status_label') else None)
        except Exception as e:
            error_msg = f"Bestellung konnte nicht erstellt werden: {str(e)}"
            self.after(0, lambda err_msg=error_msg: msgbox.showerror("Fehler", err_msg, parent=self)) # Pass error message correctly to lambda
            self.after(0, lambda err_msg=error_msg: self.master.status_label.configure(text=err_msg, text_color="red") if hasattr(self.master, 'status_label') else None)
        finally:
            # Ensure the status label on main window is eventually cleared or set to a neutral message if not success/error
            # For example, after a delay or if the user closes the create order window manually before completion.
            # This part might need more sophisticated handling depending on desired UX.
            pass


class EditProductDialog(ctk.CTkToplevel):
    def __init__(self, parent, product_data):
        super().__init__(parent)

        # Make a copy to avoid modifying the original data directly if cancelled
        self.product_data = product_data.copy()
        self.result = None

        self.title("Produkt bearbeiten")
        self.geometry("400x300") # Increased height for better spacing
        self.resizable(False, False)
        self.transient(parent)

        self.setup_ui()
        self.update_idletasks()
        self.after(1, self.grab_set)
        self.focus_force()


    def setup_ui(self):
        """UI für Produktbearbeitung"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title_label = ctk.CTkLabel(
            main_frame,
            text=f"Produkt bearbeiten: {self.product_data.get('name', 'N/A')}",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(10, 20)) # Adjusted padding

        input_frame = ctk.CTkFrame(main_frame)
        input_frame.pack(fill="x", padx=10, pady=(0, 10)) # Adjusted padding

        # Menge
        ctk.CTkLabel(input_frame, text="Menge:").grid(row=0, column=0, sticky="w", padx=(0,10), pady=(0,15))
        self.quantity_entry = ctk.CTkEntry(input_frame)
        self.quantity_entry.grid(row=0, column=1, sticky="ew", pady=(0,15))
        self.quantity_entry.insert(0, str(self.product_data.get('quantity', 1)))

        # Preis (bearbeitbar nur für benutzerdefinierte Produkte oder wenn Preis im product_data vorhanden ist)
        # Custom products or products added without a fixed ID might allow price editing.
        # Regular WooCommerce products usually get their price from the catalog.
        # For this dialog, we'll assume 'is_custom_product' flag correctly dictates price editability.
        if self.product_data.get('is_custom_product', False):
            ctk.CTkLabel(input_frame, text="Einzelpreis (€):").grid(row=1, column=0, sticky="w", padx=(0,10), pady=(0,15))
            self.price_entry = ctk.CTkEntry(input_frame)
            self.price_entry.grid(row=1, column=1, sticky="ew", pady=(0,15))
            self.price_entry.insert(0, f"{float(self.product_data.get('price', 0.0)):.2f}")
        else:
            # Display price but make it clear it's not editable here for standard products
            ctk.CTkLabel(input_frame, text="Einzelpreis (€):").grid(row=1, column=0, sticky="w", padx=(0,10), pady=(0,15))
            price_display = ctk.CTkLabel(input_frame, text=f"{float(self.product_data.get('price', 0.0)):.2f} (nicht bearbeitbar)")
            price_display.grid(row=1, column=1, sticky="ew", pady=(0,15))
            self.price_entry = None

        input_frame.grid_columnconfigure(1, weight=1)


        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=(20, 10)) # Adjusted padding

        save_button = ctk.CTkButton(
            button_frame,
            text="Speichern",
            command=self.save_changes
        )
        save_button.pack(side="left", expand=True, padx=5, pady=5)

        cancel_button = ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            command=self.destroy
        )
        cancel_button.pack(side="right", expand=True, padx=5, pady=5)

    def save_changes(self):
        """Änderungen speichern"""
        try:
            new_quantity = int(self.quantity_entry.get())
            if new_quantity <= 0:
                msgbox.showerror("Fehler", "Menge muss größer als 0 sein.", parent=self)
                return

            self.result = {'quantity': new_quantity}

            if self.price_entry: # Only if price entry exists (i.e., for custom/editable products)
                new_price_str = self.price_entry.get()
                try:
                    new_price = float(new_price_str)
                    if new_price < 0:
                        msgbox.showerror("Fehler", "Preis muss größer oder gleich 0 sein.", parent=self)
                        return
                    self.result['price'] = new_price
                except ValueError:
                    msgbox.showerror("Fehler", "Ungültiger Preis eingegeben. Bitte eine Zahl eingeben.", parent=self)
                    return
            elif 'price' in self.product_data: # If price entry is disabled, keep original price
                 self.result['price'] = float(self.product_data.get('price',0.0))


            self.destroy()

        except ValueError:
            msgbox.showerror("Fehler", "Ungültige Menge eingegeben. Bitte eine ganze Zahl eingeben.", parent=self)


class CustomProductDialog(ctk.CTkToplevel): # This class seems to be duplicated, ensure correct one is used. Assuming the one from product_search_dialog.py is primary for adding new custom products.
                                          # The one defined below might be an older version or intended for a different purpose.
                                          # For this fix, I am assuming this one is not the primary one used by "add_custom_product" in ProductSearchDialog.
                                          # If this is used by CreateOrderWindow directly, it might need similar UI fixes as EditProductDialog.
    def __init__(self, parent):
        super().__init__(parent)

        self.result = None

        self.title("Benutzerdefiniertes Produkt")
        self.geometry("400x350") # Increased height
        self.resizable(False, False)
        self.transient(parent)

        self.setup_ui()
        self.update_idletasks()
        self.after(1, self.grab_set)
        self.focus_force()


    def setup_ui(self):
        """UI für benutzerdefiniertes Produkt"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title_label = ctk.CTkLabel(
            main_frame,
            text="Benutzerdefiniertes Produkt",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(10,15))

        input_frame = ctk.CTkFrame(main_frame)
        input_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Produktname
        ctk.CTkLabel(input_frame, text="Produktname:").grid(row=0, column=0, sticky="w", padx=(0,10), pady=(0,5))
        self.name_entry = ctk.CTkEntry(input_frame, placeholder_text="Name des Produkts")
        self.name_entry.grid(row=0, column=1, sticky="ew", pady=(0,10))

        # Preis
        ctk.CTkLabel(input_frame, text="Preis (€):").grid(row=1, column=0, sticky="w", padx=(0,10), pady=(0,5))
        self.price_entry = ctk.CTkEntry(input_frame, placeholder_text="0.00")
        self.price_entry.grid(row=1, column=1, sticky="ew", pady=(0,10))

        # Menge
        ctk.CTkLabel(input_frame, text="Menge:").grid(row=2, column=0, sticky="w", padx=(0,10), pady=(0,5))
        self.quantity_entry = ctk.CTkEntry(input_frame) # Removed width=80 to allow expansion
        self.quantity_entry.grid(row=2, column=1, sticky="ew", pady=(0,15))
        self.quantity_entry.insert(0, "1")

        input_frame.grid_columnconfigure(1, weight=1)


        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=(15,10))

        ok_button = ctk.CTkButton( button_frame, text="OK", command=self.ok_clicked )
        ok_button.pack(side="left", expand=True, padx=5, pady=5)

        # "Egal" Button - consider if this button's logic is still desired or if stricter validation is preferred.
        # For this example, keeping its functionality.
        anyway_button = ctk.CTkButton( button_frame, text="Egal (mit Standardwerten)", command=self.anyway_clicked)
        anyway_button.pack(side="left", expand=True, padx=5, pady=5)

        cancel_button = ctk.CTkButton( button_frame, text="Abbrechen", command=self.destroy)
        cancel_button.pack(side="right", expand=True, padx=5, pady=5)

    def ok_clicked(self):
        """OK Button geklickt - führt strikte Validierung durch"""
        try:
            name = self.name_entry.get().strip()
            price_str = self.price_entry.get().strip()
            quantity_str = self.quantity_entry.get().strip()


            if not name:
                msgbox.showerror("Fehler", "Produktname ist erforderlich.", parent=self)
                return

            if not price_str:
                msgbox.showerror("Fehler", "Preis ist erforderlich.", parent=self)
                return
            price = float(price_str)

            if not quantity_str:
                 msgbox.showerror("Fehler", "Menge ist erforderlich.", parent=self)
                 return
            quantity = int(quantity_str)


            if price < 0:
                msgbox.showerror("Fehler", "Preis muss größer oder gleich 0 sein.", parent=self)
                return

            if quantity <= 0:
                msgbox.showerror("Fehler", "Menge muss größer als 0 sein.", parent=self)
                return

            self.result = {
                'name': name,
                'price': price,
                'quantity': quantity,
                'is_custom_product': True,
                'id': 0,
                'sku': 'CUSTOM'
            }
            self.destroy()

        except ValueError:
            msgbox.showerror("Fehler", "Ungültiger Preis oder Menge. Bitte geben Sie Zahlen ein.", parent=self)

    def anyway_clicked(self):
        """Egal Button geklickt - versucht Daten zu speichern, auch wenn sie unvollständig sind, mit Warnung"""
        name = self.name_entry.get().strip()
        price_str = self.price_entry.get().strip()
        quantity_str = self.quantity_entry.get().strip()

        warning_messages = []
        final_name = name
        final_price = 0.0
        final_quantity = 1

        if not final_name:
            warning_messages.append("Produktname ist leer. Wird auf 'Benutzerdefiniertes Produkt (unbenannt)' gesetzt.")
            final_name = "Benutzerdefiniertes Produkt (unbenannt)"

        try:
            final_price = float(price_str if price_str else "0")
            if final_price < 0:
                warning_messages.append(f"Preis ({price_str}) ist negativ. Wird auf 0.0 gesetzt.")
                final_price = 0.0
        except ValueError:
            warning_messages.append(f"Ungültiger Preis '{price_str}'. Wird auf 0.0 gesetzt.")
            final_price = 0.0

        try:
            final_quantity = int(quantity_str if quantity_str else "1")
            if final_quantity <= 0:
                warning_messages.append(f"Menge ({quantity_str}) ist Null oder negativ. Wird auf 1 gesetzt.")
                final_quantity = 1
        except ValueError:
            warning_messages.append(f"Ungültige Menge '{quantity_str}'. Wird auf 1 gesetzt.")
            final_quantity = 1

        if warning_messages:
            full_warning = "Folgende Probleme wurden erkannt und Standardwerte verwendet:\n\n" + "\n".join(warning_messages) + "\n\nMöchten Sie trotzdem fortfahren?"
            if not msgbox.askyesno("Warnung", full_warning, parent=self):
                return

        self.result = {
            'name': final_name,
            'price': final_price,
            'quantity': final_quantity,
            'is_custom_product': True,
            'id': 0,
            'sku': 'CUSTOM'
        }
        self.destroy()
import customtkinter as ctk
from main_window import MainWindow
from config import Config

def main():
    # CustomTkinter Konfiguration
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # Hauptfenster erstellen und starten
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
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
# Updated history_window.py
import customtkinter as ctk
import tkinter.messagebox as msgbox
from tkinter import ttk
import threading
from datetime import datetime

class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, parent, woo_api):
        super().__init__(parent)

        self.woo_api = woo_api
        self.orders = []
        self.sort_column = "ID"
        self.sort_direction = "descending" # "ascending" or "descending"

        self.title("Bestellverlauf")
        self.geometry("1000x600")
        self.resizable(True, True)
        self.transient(parent)

        self.setup_ui()
        self.update_idletasks()
        self.grab_set()

        self.load_orders()

    def setup_ui(self):
        """UI einrichten"""
        title_label = ctk.CTkLabel(
            self,
            text="Bestellverlauf",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)

        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(filter_frame, text="Status Filter:").pack(side="left", padx=10, pady=10)
        self.status_filter = ctk.CTkComboBox(
            filter_frame,
            values=["Alle", "pending", "processing", "on-hold", "completed", "cancelled", "refunded", "failed"],
            command=self.on_filter_change # Change to trigger reload
        )
        self.status_filter.pack(side="left", padx=10, pady=10)
        self.status_filter.set("Alle")

        refresh_button = ctk.CTkButton(
            filter_frame,
            text="Aktualisieren",
            command=self.load_orders
        )
        refresh_button.pack(side="right", padx=10, pady=10)

        self.setup_orders_table()
        self.setup_details_section()

    def setup_orders_table(self):
        """Bestellungstabelle einrichten"""
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        columns = ("ID", "Datum", "Status", "Kunde", "Summe")
        self.orders_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.orders_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(c))
            self.orders_tree.column(col, width=100, anchor="w")

        self.orders_tree.column("ID", width=80)
        self.orders_tree.column("Datum", width=100)
        self.orders_tree.column("Status", width=100)
        self.orders_tree.column("Kunde", width=200)
        self.orders_tree.column("Summe", width=100, anchor="e") # Right align sum

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.orders_tree.yview)
        self.orders_tree.configure(yscrollcommand=scrollbar.set)

        self.orders_tree.bind("<<TreeviewSelect>>", self.on_order_select)

        self.orders_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def setup_details_section(self):
        """Details Sektion einrichten"""
        details_frame = ctk.CTkFrame(self)
        details_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            details_frame,
            text="Bestelldetails",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.details_textbox = ctk.CTkTextbox(details_frame, height=150)
        self.details_textbox.pack(fill="x", padx=20, pady=(0, 20))

        button_frame = ctk.CTkFrame(details_frame)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.change_status_button = ctk.CTkButton(
            button_frame,
            text="Status ändern",
            command=self.change_order_status,
            state="disabled"
        )
        self.change_status_button.pack(side="left", padx=10, pady=10)

        self.export_button = ctk.CTkButton( # Renamed for clarity
            button_frame,
            text="Details exportieren",
            command=self.export_order_details,
            state="disabled"
        )
        self.export_button.pack(side="left", padx=10, pady=10)

        close_button = ctk.CTkButton(
            button_frame,
            text="Schließen",
            command=self.destroy
        )
        close_button.pack(side="right", padx=10, pady=10)

    def load_orders(self):
        """Bestellungen laden (und optional filtern)"""
        def load_in_background():
            try:
                self.after(0, lambda: self.show_loading(True))

                # Get filter status
                status_filter = self.status_filter.get()
                params = {'per_page': 100}
                if status_filter != "Alle":
                    params['status'] = status_filter

                self.orders = self.woo_api.get_orders(**params) # Pass params

                self.after(0, self.update_orders_display)
                self.after(0, lambda: self.show_loading(False))

            except Exception as e:
                self.after(0, lambda: msgbox.showerror("Fehler", f"Bestellungen konnten nicht geladen werden: {e}"))
                self.after(0, lambda: self.show_loading(False))

        threading.Thread(target=load_in_background, daemon=True).start()

    def on_filter_change(self, selected_value):
        """Wird aufgerufen, wenn der Statusfilter geändert wird."""
        self.load_orders() # Reload orders with new filter

    def show_loading(self, show):
        """Loading Indicator anzeigen/verstecken"""
        if show:
            for item in self.orders_tree.get_children():
                self.orders_tree.delete(item)
            self.details_textbox.delete(1.0, 'end')
            self.details_textbox.insert(1.0, "Bestellungen werden geladen...")
            self.change_status_button.configure(state="disabled")
            self.export_button.configure(state="disabled")
        else:
            self.details_textbox.delete(1.0, 'end') # Clear loading message
            # Re-enable buttons if an order is selected after loading
            if self.orders_tree.selection():
                self.change_status_button.configure(state="normal")
                self.export_button.configure(state="normal")


    def update_orders_display(self):
        """Bestellungsanzeige aktualisieren und sortieren"""
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)

        # Prepare items for sorting
        display_items = []
        for order in self.orders:
            billing = order.get('billing', {})
            customer_name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
            if not customer_name:
                customer_name = "Gast"

            order_date = order.get('date_created', '')
            if order_date:
                try:
                    dt = datetime.fromisoformat(order_date.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%Y-%m-%d %H:%M:%S') # Use full datetime for accurate sorting
                except:
                    formatted_date = order_date[:10]
            else:
                formatted_date = "Unbekannt"

            total = float(order.get('total', '0'))
            currency_symbol = order.get('currency_symbol', '€')

            # Store original order object with the item for easy lookup later
            display_items.append({
                "id": order.get('id', ''),
                "date": formatted_date,
                "status": order.get('status', '').title(),
                "customer": customer_name,
                "total": total, # Use float for sorting
                "original_order": order # Keep reference to the full order data
            })

        # Sort the items
        self._sort_display_items(display_items)

        # Insert sorted items into treeview
        for item_data in display_items:
            self.orders_tree.insert("", "end", values=(
                item_data["id"],
                item_data["date"][:10], # Display only date for brevity in table
                item_data["status"],
                item_data["customer"],
                f"{currency_symbol}{item_data['total']:.2f}"
            ), tags=(str(item_data["id"]))) # Use order ID as tag for easy lookup


    def _sort_display_items(self, items):
        """Hilfsfunktion zum Sortieren der angezeigten Elemente."""
        col_map = {
            "ID": lambda x: int(x["id"]), # Ensure numeric sort
            "Datum": lambda x: datetime.fromisoformat(x["date"]),
            "Status": lambda x: x["status"].lower(),
            "Kunde": lambda x: x["customer"].lower(),
            "Summe": lambda x: x["total"]
        }
        key_func = col_map.get(self.sort_column)

        if key_func:
            items.sort(key=key_func, reverse=(self.sort_direction == "descending"))

    def sort_treeview(self, col):
        """Sortiert die Treeview nach der angeklickten Spalte."""
        if self.sort_column == col:
            self.sort_direction = "ascending" if self.sort_direction == "descending" else "descending"
        else:
            self.sort_column = col
            self.sort_direction = "ascending" # Default to ascending for new column

        # Reload orders to re-sort (can be optimized to sort existing `self.orders` if all data is loaded)
        self.update_orders_display() # Re-render with new sort order


    def on_order_select(self, event):
        """Bestellung ausgewählt"""
        selection = self.orders_tree.selection()
        if not selection:
            self.change_status_button.configure(state="disabled")
            self.export_button.configure(state="disabled")
            self.details_textbox.delete(1.0, 'end')
            return

        item = selection[0]
        order_id = self.orders_tree.item(item, 'tags')[0] # Retrieve order ID from tags

        selected_order = next((o for o in self.orders if str(o['id']) == str(order_id)), None)

        if selected_order:
            self.show_order_details(selected_order)
            self.change_status_button.configure(state="normal")
            self.export_button.configure(state="normal")
            self.current_order = selected_order # Store current order for status change/export
        else:
            self.change_status_button.configure(state="disabled")
            self.export_button.configure(state="disabled")
            self.details_textbox.delete(1.0, 'end')


    def show_order_details(self, order):
        """Bestelldetails anzeigen (unchanged logic)"""
        self.details_textbox.delete(1.0, 'end')

        details = f"""BESTELLDETAILS
{'='*50}

Bestellnummer: {order.get('id', 'N/A')}
Datum: {order.get('date_created', 'N/A')[:10]}
Status: {order.get('status', 'N/A').title()}
Summe: {order.get('currency_symbol', '€')}{order.get('total', '0')}

RECHNUNGSADRESSE:
{'-'*20}
"""

        billing = order.get('billing', {})
        details += f"""Name: {billing.get('first_name', '')} {billing.get('last_name', '')}
Firma: {billing.get('company', 'N/A')}
Adresse: {billing.get('address_1', '')} {billing.get('address_2', '')}
PLZ/Ort: {billing.get('postcode', '')} {billing.get('city', '')}
Land: {billing.get('country', 'N/A')}
Email: {billing.get('email', 'N/A')}
Telefon: {billing.get('phone', 'N/A')}

PRODUKTE:
{'-'*20}
"""

        line_items = order.get('line_items', [])
        for item in line_items:
            details += f"• {item.get('name', 'N/A')} - Menge: {item.get('quantity', 0)} - Preis: {order.get('currency_symbol', '€')}{item.get('total', '0')}\n"

        shipping_lines = order.get('shipping_lines', [])
        if shipping_lines:
            details += f"\nVERSAND:\n{'-'*20}\n"
            for shipping in shipping_lines:
                details += f"• {shipping.get('method_title', 'N/A')}: {order.get('currency_symbol', '€')}{shipping.get('total', '0')}\n"

        details += f"""
ZAHLUNG:
{'-'*20}
Zahlungsart: {order.get('payment_method_title', 'N/A')}
Transaktions-ID: {order.get('transaction_id', 'N/A')}
"""

        customer_note = order.get('customer_note', '')
        if customer_note:
            details += f"\nKUNDENNOTIZ:\n{'-'*20}\n{customer_note}\n"

        self.details_textbox.insert(1.0, details)

    def change_order_status(self):
        """Bestellstatus ändern"""
        if not hasattr(self, 'current_order') or not self.current_order:
            msgbox.showwarning("Warnung", "Bitte wählen Sie zuerst eine Bestellung aus.")
            return

        dialog = StatusChangeDialog(self, self.current_order.get('status', 'pending'))
        if dialog.result:
            new_status = dialog.result
            self.update_order_status(self.current_order.get('id'), new_status)

    def update_order_status(self, order_id, new_status):
        """Bestellstatus bei WooCommerce aktualisieren"""
        def update_in_background():
            try:
                self.after(0, lambda: self.show_loading(True)) # Show loading during update
                update_data = {'status': new_status}
                result = self.woo_api._make_request('PUT', f'orders/{order_id}', update_data)

                if result:
                    self.after(0, lambda: msgbox.showinfo("Erfolg", f"Status wurde auf '{new_status}' geändert"))
                    self.after(0, self.load_orders)  # Bestellungen neu laden
                else:
                    self.after(0, lambda: msgbox.showerror("Fehler", "Status konnte nicht geändert werden"))

            except Exception as e:
                self.after(0, lambda: msgbox.showerror("Fehler", f"Fehler beim Ändern des Status: {e}"))
            finally:
                self.after(0, lambda: self.show_loading(False)) # Hide loading regardless of success/failure


        threading.Thread(target=update_in_background, daemon=True).start()

    def export_order_details(self):
        """Bestelldetails exportieren"""
        if not hasattr(self, 'current_order') or not self.current_order:
            msgbox.showwarning("Warnung", "Keine Bestellung ausgewählt")
            return

        try:
            from tkinter import filedialog
            import json

            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
            )

            if filename:
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.current_order, f, indent=2, ensure_ascii=False)
                else:
                    details_text = self.details_textbox.get(1.0, 'end')
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(details_text)

                msgbox.showinfo("Erfolg", f"Bestelldetails wurden in {filename} gespeichert")

        except Exception as e:
            msgbox.showerror("Fehler", f"Export fehlgeschlagen: {e}")


class StatusChangeDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_status):
        super().__init__(parent)

        self.result = None
        self.current_status = current_status

        self.title("Status ändern")
        self.geometry("300x200")
        self.resizable(False, False)
        self.transient(parent)

        self.setup_ui()
        self.update_idletasks()
        self.grab_set()

    def setup_ui(self):
        """UI für Status-Änderung"""
        title_label = ctk.CTkLabel(
            self,
            text="Neuen Status wählen",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=20)

        current_label = ctk.CTkLabel(
            self,
            text=f"Aktueller Status: {self.current_status.title()}"
        )
        current_label.pack(pady=10)

        self.status_combobox = ctk.CTkComboBox(
            self,
            values=["pending", "processing", "on-hold", "completed", "cancelled", "refunded", "failed"]
        )
        self.status_combobox.pack(pady=20)
        self.status_combobox.set(self.current_status) # Changed combobox to self.status_combobox

        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=20)

        ok_button = ctk.CTkButton(
            button_frame,
            text="Ändern",
            command=self.ok_clicked
        )
        ok_button.pack(side="left", padx=10)

        cancel_button = ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            command=self.destroy
        )
        cancel_button.pack(side="right", padx=10)

    def ok_clicked(self):
        """OK Button geklickt"""
        new_status = self.status_combobox.get()
        if new_status != self.current_status:
            self.result = new_status
        self.destroy()
import customtkinter as ctk
import tkinter.messagebox as msgbox
from tkinter import ttk
import threading
from PIL import Image, ImageTk
import io
import requests

class ProductSearchDialog(ctk.CTkToplevel):
    def __init__(self, parent, woo_api):
        super().__init__(parent)
        self.woo_api = woo_api
        self.result = [] # List of selected products to return
        self.current_page = 1
        self.per_page = 10
        self.search_term = ""
        self.search_by = "name" # or "sku"
        self.total_products = 0 # To store total products for pagination

        self.title("Produkte suchen und auswählen")
        self.geometry("800x700")
        self.resizable(True, True)
        self.transient(parent)

        self.setup_ui()
        self.update_idletasks()
        self.grab_set()

        self.load_products()

    def setup_ui(self):
        """UI einrichten"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Search Bar
        search_frame = ctk.CTkFrame(main_frame)
        search_frame.pack(fill="x", pady=(0, 15))

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Produktsuche...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda event: self.perform_search())

        self.search_by_optionmenu = ctk.CTkOptionMenu(
            search_frame,
            values=["Name", "SKU"],
            command=self.set_search_by
        )
        self.search_by_optionmenu.set("Name")
        self.search_by_optionmenu.pack(side="left", padx=(0, 10))

        search_button = ctk.CTkButton(search_frame, text="Suchen", command=self.perform_search)
        search_button.pack(side="left")

        # Treeview for products
        self.products_tree = ttk.Treeview(
            main_frame,
            columns=("ID", "Produktname", "SKU", "Preis", "Lagerbestand"),
            show="headings"
        )
        self.products_tree.pack(fill="both", expand=True, pady=10)

        self.products_tree.heading("ID", text="ID")
        self.products_tree.heading("Produktname", text="Produktname")
        self.products_tree.heading("SKU", text="SKU")
        self.products_tree.heading("Preis", text="Preis (€)")
        self.products_tree.heading("Lagerbestand", text="Lagerbestand")

        self.products_tree.column("ID", width=60, stretch=False)
        self.products_tree.column("Produktname", width=250, stretch=True)
        self.products_tree.column("SKU", width=120, stretch=True)
        self.products_tree.column("Preis", width=80, stretch=False, anchor="e")
        self.products_tree.column("Lagerbestand", width=100, stretch=False, anchor="center")

        # Pagination
        pagination_frame = ctk.CTkFrame(main_frame)
        pagination_frame.pack(fill="x", pady=(10, 0))

        self.prev_button = ctk.CTkButton(pagination_frame, text="Zurück", command=self.prev_page, state="disabled")
        self.prev_button.pack(side="left", padx=(0, 10))

        self.page_label = ctk.CTkLabel(pagination_frame, text="Seite 1 / 1")
        self.page_label.pack(side="left", padx=(0, 10))

        self.next_button = ctk.CTkButton(pagination_frame, text="Weiter", command=self.next_page, state="disabled")
        self.next_button.pack(side="left")

        # Add to Order and Close Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=10)

        add_selected_button = ctk.CTkButton(button_frame, text="Ausgewählte Produkte hinzufügen", command=self.add_selected_products)
        add_selected_button.pack(side="left", padx=10)

        add_custom_button = ctk.CTkButton(button_frame, text="Eigenes Produkt hinzufügen", command=self.add_custom_product)
        add_custom_button.pack(side="left", padx=10)

        cancel_button = ctk.CTkButton(button_frame, text="Abbrechen", command=self.destroy)
        cancel_button.pack(side="right", padx=10)

    def set_search_by(self, choice):
        self.search_by = "name" if choice == "Name" else "sku"

    def perform_search(self):
        self.search_term = self.search_entry.get()
        self.current_page = 1 # Reset page on new search
        self.load_products()

    def load_products(self):
        threading.Thread(target=self._load_products_thread, daemon=True).start()

    def _load_products_thread(self):
        self.after(0, lambda: self.show_loading(True))
        try:
            params = {
                'page': self.current_page,
                'per_page': self.per_page
            }
            if self.search_term:
                if self.search_by == "name":
                    params['search'] = self.search_term
                elif self.search_by == "sku":
                    params['sku'] = self.search_term

            products_data = self.woo_api.get_products(**params)
            self.total_products = int(self.woo_api.last_response_headers.get('X-WP-Total', 0))

            self.after(0, lambda: self.update_pagination_buttons())
            self.after(0, lambda: self.display_products(products_data))

        except Exception as e:
            self.after(0, lambda err=e: msgbox.showerror("Fehler", f"Produkte konnten nicht geladen werden: {err}"))
        finally:
            self.after(0, lambda: self.show_loading(False))

    def display_products(self, products):
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        if not products:
            self.products_tree.insert("", "end", values=("", "Keine Produkte gefunden", "", "", ""))
            return

        for product in products:
            product_id = product.get('id', 'N/A')
            name = product.get('name', 'N/A')
            sku = product.get('sku', 'N/A')

            # Robust price conversion
            price_str = product.get('price')
            price = "N/A"
            if price_str is not None:
                try:
                    price = f"{float(price_str):.2f}"
                except (ValueError, TypeError):
                    print(f"Warning: Could not convert price '{price_str}' for product ID {product_id} in ProductSearchDialog. Setting to N/A.")
                    price = "N/A"

            # Robust stock_quantity conversion
            stock_q_val = product.get('stock_quantity')
            stock_quantity = "N/A"
            if stock_q_val is not None:
                try:
                    stock_quantity = int(stock_q_val)
                except (ValueError, TypeError):
                    print(f"Warning: Could not convert stock_quantity '{stock_q_val}' for product ID {product_id} in ProductSearchDialog. Setting to N/A.")
                    stock_quantity = "N/A"

            self.products_tree.insert(
                "", "end",
                values=(product_id, name, sku, price, stock_quantity),
                iid=product_id # Use product ID as iid for easy lookup
            )

    def add_selected_products(self):
        selected_items = self.products_tree.selection()
        if not selected_items:
            msgbox.showinfo("Info", "Bitte wählen Sie mindestens ein Produkt aus.")
            return

        for item_id in selected_items:
            values = self.products_tree.item(item_id, 'values')
            product_id = values[0]
            name = values[1]
            sku = values[2]
            price_str = values[3]
            stock_quantity_str = values[4]

            price = 0.0
            try:
                price = float(price_str)
            except ValueError:
                print(f"Warning: Could not convert displayed price '{price_str}' to float for product ID {product_id}. Using 0.0.")

            stock_quantity = 0
            try:
                stock_quantity = int(stock_quantity_str)
            except ValueError:
                print(f"Warning: Could not convert displayed stock_quantity '{stock_quantity_str}' to int for product ID {product_id}. Using 0.")


            # If you need more detailed product info (e.g., images), you'd re-fetch from self.woo_api
            # or ensure they are stored when products are initially loaded.
            self.result.append({
                'id': int(product_id), # Ensure ID is int
                'name': name,
                'sku': sku,
                'price': price,
                'stock_quantity': stock_quantity,
                'quantity': 1 # Default quantity when adding to order
            })
        self.destroy()

    def add_custom_product(self):
        # Implement a dialog to get custom product details (name, price, quantity)
        dialog = CustomProductDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            custom_product = dialog.result
            custom_product['id'] = 0 # Indicate it's not a WooCommerce product ID
            custom_product['sku'] = "CUSTOM"
            custom_product['stock_quantity'] = 9999 # Arbitrarily high for custom
            custom_product['is_custom_product'] = True # Flag for later distinction
            self.result.append(custom_product)
            self.destroy()


    def show_loading(self, show):
        """Loading Indicator anzeigen/verstecken"""
        if show:
            for item in self.products_tree.get_children():
                self.products_tree.delete(item)
            self.products_tree.insert("", "end", values=("", "Produkte werden geladen...", "", "", ""))
            self.prev_button.configure(state="disabled")
            self.next_button.configure(state="disabled")
        else:
            # Check if there's a loading message before attempting to delete
            if self.products_tree.get_children() and self.products_tree.item(self.products_tree.get_children()[0])['values'][1] == "Produkte werden geladen...":
                self.products_tree.delete(self.products_tree.get_children()[0]) # Remove loading message
            self.update_pagination_buttons()

    def update_pagination_buttons(self):
        total_pages = (self.total_products + self.per_page - 1) // self.per_page if self.total_products > 0 else 1
        self.page_label.configure(text=f"Seite {self.current_page} / {total_pages}")

        self.prev_button.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_button.configure(state="normal" if self.current_page < total_pages else "disabled")

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_products()

    def next_page(self):
        total_pages = (self.total_products + self.per_page - 1) // self.per_page if self.total_products > 0 else 1
        if self.current_page < total_pages:
            self.current_page += 1
            self.load_products()

class CustomProductDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Eigenes Produkt hinzufügen")
        self.geometry("350x250")
        self.transient(parent)
        self.grab_set()
        self.result = None

        self.setup_ui()

    def setup_ui(self):
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(input_frame, text="Produktname:").pack(anchor="w", padx=10, pady=(0, 5))
        self.name_entry = ctk.CTkEntry(input_frame)
        self.name_entry.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(input_frame, text="Preis (€):").pack(anchor="w", padx=10, pady=(0, 5))
        self.price_entry = ctk.CTkEntry(input_frame)
        self.price_entry.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(input_frame, text="Menge:").pack(anchor="w", padx=10, pady=(0, 5))
        self.quantity_entry = ctk.CTkEntry(input_frame)
        self.quantity_entry.pack(fill="x", padx=10, pady=(0, 10))
        self.quantity_entry.insert(0, "1") # Default quantity

        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=10)

        save_button = ctk.CTkButton(button_frame, text="Hinzufügen", command=self.save_custom_product)
        save_button.pack(side="left", padx=10)

        cancel_button = ctk.CTkButton(button_frame, text="Abbrechen", command=self.destroy)
        cancel_button.pack(side="right", padx=10)

    def save_custom_product(self):
        name = self.name_entry.get().strip()
        price_str = self.price_entry.get().strip()
        quantity_str = self.quantity_entry.get().strip()

        if not name:
            msgbox.showerror("Fehler", "Produktname darf nicht leer sein.")
            return

        try:
            price = float(price_str)
            if price < 0:
                msgbox.showerror("Fehler", "Preis muss größer oder gleich 0 sein.")
                return
        except ValueError:
            msgbox.showerror("Fehler", "Ungültiger Preis. Bitte eine Zahl eingeben.")
            return

        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                msgbox.showerror("Fehler", "Menge muss größer als 0 sein.")
                return
        except ValueError:
            msgbox.showerror("Fehler", "Ungültige Menge. Bitte eine ganze Zahl eingeben.")
            return

        self.result = {
            'name': name,
            'price': price,
            'quantity': quantity
        }
        self.destroy()
{
    "woo_url": "",
    "consumer_key": "",
    "consumer_secret": ""
}

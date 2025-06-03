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

        # Frame for buttons (search and custom product)
        button_row_frame = ctk.CTkFrame(products_frame, fg_color="transparent") # Use transparent frame
        button_row_frame.pack(fill="x", padx=20, pady=(0, 10))

        # Button zum Öffnen des Produkt-Suchdialogs
        open_search_button = ctk.CTkButton(
            button_row_frame,
            text="Produkte suchen und hinzufügen",
            command=self.open_product_search_dialog
        )
        open_search_button.pack(side="left", padx=(0, 10)) # Pack to the left

        # Button zum Hinzufügen eines eigenen Produkts
        add_custom_product_button = ctk.CTkButton(
            button_row_frame,
            text="Eigenes Produkt hinzufügen",
            command=self.open_custom_product_dialog # New command
        )
        add_custom_product_button.pack(side="left") # Pack next to search button


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

    def open_custom_product_dialog(self):
        """Öffnet den Dialog zum Hinzufügen eines benutzerdefinierten Produkts."""
        dialog = CustomProductDialog(self)
        self.wait_window(dialog)

        if dialog.result: # If the user clicked OK or Anyway and a product was defined
            self.selected_products.append(dialog.result)
            self.update_selected_products_treeview()


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
                    print(f"Warning: Non-numeric price for product {selected_product_data.get('name')} during order creation.")

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
                    line_item['price'] = f"{current_product_price:.2f}" # Unit price for custom item, formatted to 2 decimals
                    line_item['sku'] = selected_product_data.get('sku', '') # Ensure SKU is included for custom products
                    # Explicitly add total for custom products to ensure correct calculation on WC side
                    line_item['total'] = f"{(current_product_price * quantity):.2f}"


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

            # SKU field for custom products in edit mode
            ctk.CTkLabel(input_frame, text="SKU:").grid(row=2, column=0, sticky="w", padx=(0,10), pady=(0,15))
            self.sku_entry = ctk.CTkEntry(input_frame)
            self.sku_entry.grid(row=2, column=1, sticky="ew", pady=(0,15))
            self.sku_entry.insert(0, self.product_data.get('sku', ''))

        else:
            # Display price but make it clear it's not editable here for standard products
            ctk.CTkLabel(input_frame, text="Einzelpreis (€):").grid(row=1, column=0, sticky="w", padx=(0,10), pady=(0,15))
            price_display = ctk.CTkLabel(input_frame, text=f"{float(self.product_data.get('price', 0.0)):.2f} (nicht bearbeitbar)")
            price_display.grid(row=1, column=1, sticky="ew", pady=(0,15))
            self.price_entry = None

            # Display SKU but make it clear it's not editable here for standard products
            ctk.CTkLabel(input_frame, text="SKU:").grid(row=2, column=0, sticky="w", padx=(0,10), pady=(0,15))
            sku_display = ctk.CTkLabel(input_frame, text=self.product_data.get('sku', 'N/A') + " (nicht bearbeitbar)")
            sku_display.grid(row=2, column=1, sticky="ew", pady=(0,15))
            self.sku_entry = None


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

            if self.sku_entry: # If SKU entry exists (for custom products)
                self.result['sku'] = self.sku_entry.get().strip()

            self.destroy()

        except ValueError:
            msgbox.showerror("Fehler", "Ungültige Menge eingegeben. Bitte eine ganze Zahl eingeben.", parent=self)


class CustomProductDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.result = None

        self.title("Benutzerdefiniertes Produkt")
        self.geometry("400x380") # Increased height
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
        self.quantity_entry.grid(row=2, column=1, sticky="ew", pady=(0,10))
        self.quantity_entry.insert(0, "1")

        # SKU
        ctk.CTkLabel(input_frame, text="SKU:").grid(row=3, column=0, sticky="w", padx=(0,10), pady=(0,5))
        self.sku_entry = ctk.CTkEntry(input_frame, placeholder_text="SKU")
        self.sku_entry.grid(row=3, column=1, sticky="ew", pady=(0,15))


        input_frame.grid_columnconfigure(1, weight=1)


        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=(15,10))

        ok_button = ctk.CTkButton( button_frame, text="OK", command=self.ok_clicked )
        ok_button.pack(side="left", expand=True, padx=5, pady=5)

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
            sku = self.sku_entry.get().strip() # Get SKU


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
                'price': price, # Here 'price' is a float
                'quantity': quantity,
                'is_custom_product': True,
                'id': 0,
                'sku': sku
            }
            self.destroy()

        except ValueError:
            msgbox.showerror("Fehler", "Ungültiger Preis oder Menge. Bitte geben Sie Zahlen ein.", parent=self)

    def anyway_clicked(self):
        """Egal Button geklickt - versucht Daten zu speichern, auch wenn sie unvollständig sind, mit Warnung"""
        name = self.name_entry.get().strip()
        price_str = self.price_entry.get().strip()
        quantity_str = self.quantity_entry.get().strip()
        sku = self.sku_entry.get().strip() # Get SKU

        warning_messages = []
        final_name = name
        final_price = 0.0
        final_quantity = 1
        final_sku = sku # Initialize with entered SKU

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

        if not final_sku:
            warning_messages.append("SKU ist leer. Wird auf 'CUSTOM_SKU' gesetzt.")
            final_sku = "CUSTOM_SKU"

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
            'sku': final_sku # Include the final SKU
        }
        self.destroy()

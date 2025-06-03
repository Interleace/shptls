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

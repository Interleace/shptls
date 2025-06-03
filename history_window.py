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

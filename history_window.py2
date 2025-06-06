import customtkinter as ctk
import tkinter.messagebox as msgbox
from tkinter import ttk
import threading
from datetime import datetime
import tempfile
import platform
import subprocess
import os

class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, parent, woo_api):
        super().__init__(parent)

        self.woo_api = woo_api
        self.orders = []
        self.sort_column = "ID"
        self.sort_direction = "descending"

        self.title("Bestellverlauf")
        self.geometry("1000x600")
        self.resizable(True, True)
        self.transient(parent)

        self.setup_ui()
        self.update_idletasks()
        self.grab_set()

        self.load_orders()

    def setup_ui(self):
        title_label = ctk.CTkLabel(self, text="Bestellverlauf", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=20)

        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(filter_frame, text="Status Filter:").pack(side="left", padx=10, pady=10)
        self.status_filter = ctk.CTkComboBox(
            filter_frame,
            values=["Alle", "pending", "processing", "on-hold", "completed", "cancelled", "refunded", "failed"],
            command=self.on_filter_change
        )
        self.status_filter.pack(side="left", padx=10, pady=10)
        self.status_filter.set("Alle")

        self.print_button = ctk.CTkButton(
            filter_frame,
            text="Drucken",
            command=self.print_current_invoice,
            state="disabled"
        )
        self.print_button.pack(side="left", padx=10, pady=10)

        refresh_button = ctk.CTkButton(filter_frame, text="Aktualisieren", command=self.load_orders)
        refresh_button.pack(side="right", padx=10, pady=10)

        self.setup_orders_table()
        self.setup_details_section()

    def setup_orders_table(self):
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
        self.orders_tree.column("Summe", width=100, anchor="e")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.orders_tree.yview)
        self.orders_tree.configure(yscrollcommand=scrollbar.set)

        self.orders_tree.bind("<<TreeviewSelect>>", self.on_order_select)

        self.orders_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def setup_details_section(self):
        details_frame = ctk.CTkFrame(self)
        details_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(details_frame, text="Bestelldetails", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))

        self.details_textbox = ctk.CTkTextbox(details_frame, height=150)
        self.details_textbox.pack(fill="x", padx=20, pady=(0, 20))

        button_frame = ctk.CTkFrame(details_frame)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.change_status_button = ctk.CTkButton(button_frame, text="Status ändern", command=self.change_order_status, state="disabled")
        self.change_status_button.pack(side="left", padx=10, pady=10)

        self.export_button = ctk.CTkButton(button_frame, text="Details exportieren", command=self.export_order_details, state="disabled")
        self.export_button.pack(side="left", padx=10, pady=10)

        close_button = ctk.CTkButton(button_frame, text="Schließen", command=self.destroy)
        close_button.pack(side="right", padx=10, pady=10)

    def load_orders(self):
        def load_in_background():
            try:
                self.after(0, lambda: self.show_loading(True))
                status_filter = self.status_filter.get()
                params = {'per_page': 100}
                if status_filter != "Alle":
                    params['status'] = status_filter
                self.orders = self.woo_api.get_orders(**params)
                self.after(0, self.update_orders_display)
                self.after(0, lambda: self.show_loading(False))
            except Exception as e:
                self.after(0, lambda: msgbox.showerror("Fehler", f"Bestellungen konnten nicht geladen werden: {e}"))
                self.after(0, lambda: self.show_loading(False))

        threading.Thread(target=load_in_background, daemon=True).start()

    def on_filter_change(self, selected_value):
        self.load_orders()

    def show_loading(self, show):
        if show:
            for item in self.orders_tree.get_children():
                self.orders_tree.delete(item)
            self.details_textbox.delete(1.0, 'end')
            self.details_textbox.insert(1.0, "Bestellungen werden geladen...")
            self.change_status_button.configure(state="disabled")
            self.export_button.configure(state="disabled")
            self.print_button.configure(state="disabled")
        else:
            self.details_textbox.delete(1.0, 'end')
            if self.orders_tree.selection():
                self.change_status_button.configure(state="normal")
                self.export_button.configure(state="normal")
                self.print_button.configure(state="normal")

    def update_orders_display(self):
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)

        display_items = []
        for order in self.orders:
            billing = order.get('billing', {})
            customer_name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip() or "Gast"
            order_date = order.get('date_created', '')
            formatted_date = order_date[:10]
            total = float(order.get('total', '0'))
            currency_symbol = order.get('currency_symbol', '€')
            display_items.append({
                "id": order.get('id', ''),
                "date": formatted_date,
                "status": order.get('status', '').title(),
                "customer": customer_name,
                "total": total,
                "original_order": order
            })

        self._sort_display_items(display_items)

        for item in display_items:
            self.orders_tree.insert("", "end", values=(
                item["id"], item["date"], item["status"], item["customer"], f"{currency_symbol}{item['total']:.2f}"
            ), tags=(str(item["id"]),))

    def _sort_display_items(self, items):
        key_funcs = {
            "ID": lambda x: int(x["id"]),
            "Datum": lambda x: x["date"],
            "Status": lambda x: x["status"].lower(),
            "Kunde": lambda x: x["customer"].lower(),
            "Summe": lambda x: x["total"]
        }
        items.sort(key=key_funcs.get(self.sort_column, lambda x: x["id"]), reverse=self.sort_direction == "descending")

    def sort_treeview(self, col):
        self.sort_direction = "ascending" if self.sort_column == col and self.sort_direction == "descending" else "descending"
        self.sort_column = col
        self.update_orders_display()

    def on_order_select(self, event):
        selection = self.orders_tree.selection()
        if not selection:
            self.change_status_button.configure(state="disabled")
            self.export_button.configure(state="disabled")
            self.print_button.configure(state="disabled")
            self.details_textbox.delete(1.0, 'end')
            return

        order_id = self.orders_tree.item(selection[0], 'tags')[0]
        selected_order = next((o for o in self.orders if str(o['id']) == str(order_id)), None)

        if selected_order:
            self.show_order_details(selected_order)
            self.change_status_button.configure(state="normal")
            self.export_button.configure(state="normal")
            self.print_button.configure(state="normal")
            self.current_order = selected_order
        else:
            self.change_status_button.configure(state="disabled")
            self.export_button.configure(state="disabled")
            self.print_button.configure(state="disabled")
            self.details_textbox.delete(1.0, 'end')

    def show_order_details(self, order):
        self.details_textbox.delete(1.0, 'end')
        self.details_textbox.insert(1.0, f"Bestellnummer: {order.get('id')}\nStatus: {order.get('status')}\nSumme: {order.get('total')} €")

    def print_current_invoice(self):
        if not hasattr(self, 'current_order') or not self.current_order:
            msgbox.showwarning("Warnung", "Keine Bestellung ausgewählt.")
            return

        order_id = self.current_order.get("id")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                pdf_path = tmp.name

            self.woo_api.download_invoice_pdf(order_id, pdf_path)

            system = platform.system()
            if system == "Windows":
                os.startfile(pdf_path, "print")
            elif system == "Linux":
                subprocess.run(["lp", pdf_path], check=False)
            else:
                msgbox.showinfo("Nicht unterstützt", f"Drucken unter {system} wird nicht automatisch unterstützt.")

        except Exception as e:
            msgbox.showerror("Fehler beim Drucken", f"Die Rechnung konnte nicht gedruckt werden:\n{e}")

    def change_order_status(self):
        pass  # Placeholder

    def export_order_details(self):
        pass  # Placeholder

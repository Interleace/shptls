import customtkinter as ctk
import tkinter.messagebox as msgbox
from tkinter import ttk
import threading
from datetime import datetime
import tempfile
import platform
import subprocess
import os
import webbrowser

# Plattformabhängige Imports
if platform.system() == "Windows":
    try:
        import win32print
        import win32api
    except ImportError:
        # Fallback falls win32-Module nicht verfügbar sind
        class DummyWin32:
            def __getattr__(self, name):
                def dummy_function(*args, **kwargs):
                    print(f"Dummy-Funktion '{name}' aufgerufen mit args={args}, kwargs={kwargs}")
                    return None
                return dummy_function
        win32print = DummyWin32()
        win32api = DummyWin32()
else:
    # Dummy-Objekte für Nicht-Windows-Systeme
    class DummyWin32:
        def __getattr__(self, name):
            def dummy_function(*args, **kwargs):
                print(f"Dummy-Funktion '{name}' aufgerufen mit args={args}, kwargs={kwargs}")
                return None
            return dummy_function
    win32print = DummyWin32()
    win32api = DummyWin32()

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
        pdf_path = None
        try:
            # Sicherere Erstellung der temporären Datei
            import tempfile
            import time

            # Erstelle temporäre Datei mit eindeutigem Namen
            temp_dir = tempfile.gettempdir()
            pdf_filename = f"invoice_{order_id}_{int(time.time())}.pdf"
            pdf_path = os.path.join(temp_dir, pdf_filename)

            # Download der PDF
            self.woo_api.download_invoice_pdf(order_id, pdf_path)

            # Warte kurz und validiere die PDF-Datei
            time.sleep(0.5)  # Kurze Pause um sicherzustellen, dass die Datei vollständig geschrieben ist

            if not os.path.exists(pdf_path):
                raise Exception("PDF-Datei wurde nicht erstellt")

            if os.path.getsize(pdf_path) == 0:
                raise Exception("PDF-Datei ist leer")

            # Versuche die PDF-Datei zu validieren (einfacher Check)
            self._validate_pdf_file(pdf_path)

            self._print_pdf_platform_specific(pdf_path)

        except Exception as e:
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except:
                    pass
            msgbox.showerror("Fehler beim Drucken", f"Die Rechnung konnte nicht gedruckt werden:\n{e}")

    def _validate_pdf_file(self, pdf_path):
        """Einfache PDF-Validierung"""
        try:
            with open(pdf_path, 'rb') as f:
                # Lese die ersten paar Bytes
                header = f.read(8)
                if not header.startswith(b'%PDF-'):
                    raise Exception("Datei ist keine gültige PDF")

                # Gehe zum Ende der Datei
                f.seek(-10, 2)  # 10 Bytes vom Ende
                footer = f.read()
                if b'%%EOF' not in footer:
                    raise Exception("PDF-Datei ist unvollständig")

        except Exception as e:
            raise Exception(f"PDF-Validierung fehlgeschlagen: {e}")

    def _print_pdf_platform_specific(self, pdf_path):
        """Plattformspezifische Druckfunktion"""
        system = platform.system()

        if system == "Windows":
            try:
                # Versuche direktes Drucken über Windows API
                win32api.ShellExecute(
                    0,
                    "print",
                    pdf_path,
                    None,
                    ".",
                    0
                )
                msgbox.showinfo("Drucken", "Druckauftrag wurde an den Standarddrucker gesendet.")
                return
            except Exception as e:
                print(f"Windows-spezifisches Drucken fehlgeschlagen: {e}")
                # Fallback zu Browser-Öffnung
                self._open_pdf_in_browser(pdf_path, "Windows-Drucken fehlgeschlagen")

        elif system == "Linux":
            try:
                # Versuche Linux-spezifisches Drucken über lp
                result = subprocess.run(["lp", pdf_path], check=True, capture_output=True, text=True)
                msgbox.showinfo("Drucken", "Druckauftrag wurde erfolgreich gesendet.")
                return
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"Linux-spezifisches Drucken fehlgeschlagen: {e}")
                # Fallback zu Browser-Öffnung
                self._open_pdf_in_browser(pdf_path, "Linux-Drucken fehlgeschlagen")

        elif system == "Darwin":  # macOS
            try:
                # Versuche macOS-spezifisches Drucken über lpr
                result = subprocess.run(["lpr", pdf_path], check=True, capture_output=True, text=True)
                msgbox.showinfo("Drucken", "Druckauftrag wurde erfolgreich gesendet.")
                return
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"macOS-spezifisches Drucken fehlgeschlagen: {e}")
                # Fallback zu Browser-Öffnung
                self._open_pdf_in_browser(pdf_path, "macOS-Drucken fehlgeschlagen")
        else:
            # Unbekanntes System
            self._open_pdf_in_browser(pdf_path, f"System '{system}' wird nicht unterstützt")

    def _open_pdf_in_browser(self, pdf_path, reason=""):
        """Fallback: PDF im Browser öffnen"""
        system = platform.system()

        if system == "Linux":
            # Unter Linux explizit Browser-Befehle versuchen mit zusätzlicher Sicherheit
            browsers = [
                ['chromium-browser', '--new-window'],
                ['google-chrome', '--new-window'],
                ['firefox', '--new-window'],
                ['chromium', '--new-window']
            ]
            browser_opened = False

            for browser_cmd in browsers:
                try:
                    # Starte Browser im Hintergrund und warte nicht auf Beendigung
                    process = subprocess.Popen(
                        browser_cmd + [f"file://{pdf_path}"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        preexec_fn=os.setsid  # Starte in neuer Session
                    )
                    browser_opened = True
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue

            if not browser_opened:
                # Fallback zu PDF-Viewer wenn kein Browser funktioniert
                pdf_viewers = ['evince', 'okular', 'xpdf', 'mupdf']
                for viewer in pdf_viewers:
                    try:
                        subprocess.Popen([viewer, pdf_path],
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL,
                                       preexec_fn=os.setsid)
                        browser_opened = True
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue

            if not browser_opened:
                # Letzter Fallback zu xdg-open
                try:
                    subprocess.Popen(['xdg-open', pdf_path],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL,
                                   preexec_fn=os.setsid)
                    browser_opened = True
                except:
                    pass

            if browser_opened:
                message = "Die Rechnung wurde geöffnet. Bitte drucke sie dort manuell."
                if reason:
                    message = f"{reason}. {message}"
                msgbox.showinfo("PDF geöffnet", message)
            else:
                msgbox.showerror("Fehler", f"Kein PDF-Viewer gefunden. Datei gespeichert unter: {pdf_path}")

        else:
            # Für Windows und macOS: Standard webbrowser-Modul verwenden
            try:
                webbrowser.open_new(f"file://{pdf_path}")
                message = "Die Rechnung wurde im Browser geöffnet. Bitte drucke sie dort manuell."
                if reason:
                    message = f"{reason}. {message}"
                msgbox.showinfo("Drucken im Browser", message)
            except Exception as e:
                msgbox.showerror("Fehler", f"PDF konnte nicht geöffnet werden: {e}")

    def _get_default_printer_info(self):
        """Gibt Informationen über den Standarddrucker zurück (nur für Debugging/Info)"""
        system = platform.system()

        if system == "Windows":
            try:
                printer_name = win32print.GetDefaultPrinter()
                return f"Windows-Standarddrucker: {printer_name}"
            except Exception as e:
                return f"Konnte Windows-Drucker nicht ermitteln: {e}"

        elif system == "Linux":
            try:
                result = subprocess.run(["lpstat", "-d"], capture_output=True, text=True, check=True)
                return f"Linux-Standarddrucker: {result.stdout.strip()}"
            except Exception as e:
                return f"Konnte Linux-Drucker nicht ermitteln: {e}"

        elif system == "Darwin":
            try:
                result = subprocess.run(["lpstat", "-d"], capture_output=True, text=True, check=True)
                return f"macOS-Standarddrucker: {result.stdout.strip()}"
            except Exception as e:
                return f"Konnte macOS-Drucker nicht ermitteln: {e}"
        else:
            return f"Druckerinformationen für '{system}' nicht verfügbar"

    def change_order_status(self):
        pass  # Placeholder

    def export_order_details(self):
        pass  # Placeholder

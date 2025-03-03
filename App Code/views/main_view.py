# views/main_view.py

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
from models.order_item import OrderItem
from models.order import Order
from models.order_status import OrderStatus
from utils.email_util import send_email
import folium
import threading
import webbrowser
import tempfile
from config import ADMIN_PASSWORD
import os
import stripe
from dotenv import load_dotenv
from tkcalendar import Calendar
import time
from datetime import datetime

load_dotenv()
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY

class MainView:
    def __init__(self, root, controller):
        """
        Initialize the main view of the application, set up UI, styles, and start reminder checking.

        Parameters:
            root (Tk): The root Tkinter window.
            controller: The application controller managing data and APIs.
        """
        self.root = root
        self.controller = controller
        self.admin_authenticated = False
        self.plus_unlocked = False  # Indicates if the Plus Plan is activated

        # A list of reminders as tuples (datetime, text)
        self.reminders = []
        self.check_reminders = True
        self.start_reminder_checker()  # Start background thread to check reminders

        # Set up main frame and layout
        self.main_frame = tk.Frame(root, bg='#f0f4f8')
        self.main_frame.grid(row=0, column=0, sticky='nsew')
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        # Header frame with branding
        self.header_frame = tk.Frame(self.main_frame, bg='#003366', height=60)
        self.header_frame.grid(row=0, column=0, sticky='ew')
        self.main_frame.rowconfigure(0, weight=0)
        self.main_frame.columnconfigure(0, weight=1)

        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#f0f4f8')
        self.style.configure('TLabel', background='#f0f4f8', font=("Helvetica", 12))
        self.style.configure('TButton', font=("Helvetica", 12))
        self.style.configure('Header.TLabel', background='#003366', foreground='white', font=("Helvetica", 18, "bold"))
        self.style.configure('SubHeader.TLabel', background='#003366', foreground='white', font=("Helvetica", 12))

        # Load icons
        try:
            icon_size = (24, 24)
            home_image = Image.open('icons/home.png').resize(icon_size, Image.LANCZOS)
            self.home_icon = ImageTk.PhotoImage(home_image)

            order_image = Image.open('icons/order.png').resize(icon_size, Image.LANCZOS)
            self.order_icon = ImageTk.PhotoImage(order_image)

            history_image = Image.open('icons/history.png').resize(icon_size, Image.LANCZOS)
            self.history_icon = ImageTk.PhotoImage(history_image)

            track_image = Image.open('icons/track.png').resize(icon_size, Image.LANCZOS)
            self.track_icon = ImageTk.PhotoImage(track_image)

            inventory_image = Image.open('icons/inventory.png').resize(icon_size, Image.LANCZOS)
            self.inventory_icon = ImageTk.PhotoImage(inventory_image)

            self.icon_images = [home_image, order_image, history_image, track_image, inventory_image]
        except Exception as e:
            print(f"Error loading icons: {e}")
            # Fallback if icons not found
            self.home_icon = tk.PhotoImage()
            self.order_icon = tk.PhotoImage()
            self.history_icon = tk.PhotoImage()
            self.track_icon = tk.PhotoImage()
            self.inventory_icon = tk.PhotoImage()

        forestview_label = ttk.Label(self.header_frame, text="ForestView Parts & Tracking", style='Header.TLabel')
        forestview_label.grid(row=0, column=0, padx=(10, 5), sticky='w')

        # Set up all tabs
        self.setup_tabs()

        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w')
        self.status_bar.grid(row=1, column=0, sticky='ew')
        root.rowconfigure(1, weight=0)

    def setup_tabs(self):
        """
        Set up the main application tabs (Home, Place Order, Order History, Track Order, Inventory).
        The Calendar tab is added after plus plan is activated.
        """
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=1, column=0, sticky='nsew')
        self.main_frame.rowconfigure(1, weight=1)

        # Home tab
        self.home_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.home_tab, text='Home', image=self.home_icon, compound='left')
        self.setup_home_tab()

        # Place Order tab
        self.place_order_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.place_order_tab, text='Place Order', image=self.order_icon, compound='left')
        self.setup_place_order_tab()

        # Order History tab
        self.order_history_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.order_history_tab, text='Order History', image=self.history_icon, compound='left')
        self.setup_order_history_tab()

        # Track Order tab
        self.track_order_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.track_order_tab, text='Track Order', image=self.track_icon, compound='left')
        self.setup_track_order_tab()

        # Inventory tab
        self.inventory_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.inventory_tab, text='Inventory', image=self.inventory_icon, compound='left')
        self.setup_inventory_tab()

        self.notebook.select(self.home_tab)

    def setup_home_tab(self):
        """
        Set up the home tab, including intro text and the 'Activate Plus Plan' button.
        """
        main_frame = ttk.Frame(self.home_tab, padding=20)
        main_frame.grid(row=0, column=0, sticky='nsew')
        self.home_tab.rowconfigure(0, weight=1)
        self.home_tab.columnconfigure(0, weight=1)

        # Load and display logo if available
        try:
            logo_image = Image.open('icons/forestviewlogo.png')
            logo_image = logo_image.resize((150, 150), Image.LANCZOS)
            self.logo_icon = ImageTk.PhotoImage(logo_image)
            logo_label = tk.Label(main_frame, image=self.logo_icon, bg='#f0f4f8')
            logo_label.grid(row=0, column=1, padx=(10, 0), pady=(10, 0), sticky='ne')
        except Exception as e:
            print(f"Failed to load logo: {e}")

        # Intro text
        intro_text = (
            "Welcome to ForestView!\n\n"
            "Here you can browse automotive parts, securely pay for them, and track your orders in real-time.\n"
        )
        intro_label = ttk.Label(
            main_frame,
            text=intro_text,
            font=("Helvetica", 14),
            justify='left',
            anchor='nw'
        )
        intro_label.grid(row=0, column=0, pady=10, sticky='nw')

        # Instructions text
        instructions_text = (
            "How to Use This Application:\n"
            "1. Navigate to the 'Place Order' tab to select parts and pay securely.\n"
            "2. Check 'Track Order' to see real-time progress.\n"
            "3. View past orders in 'Order History'.\n"
            "4. Admins can manage inventory in 'Inventory'.\n\n"
            "Upgrade to our Plus Plan for additional features like the Calendar & Reminders!"
        )

        instructions_label = ttk.Label(
            main_frame,
            text=instructions_text,
            font=("Helvetica", 12),
            justify='left',
            anchor='nw'
        )
        instructions_label.grid(row=1, column=0, columnspan=2, pady=(20, 0), sticky='nw')

        # Activate Plus Plan button
        activate_button = ttk.Button(
            main_frame,
            text="Activate Plus Plan",
            command=self.activate_plus_plan
        )
        activate_button.grid(row=2, column=0, pady=20, sticky='w')

        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

    def activate_plus_plan(self):
        """
        Prompt the user for a Plus Plan key. If correct, unlock the Plus Plan features (Calendar tab).
        """
        key = simpledialog.askstring("Activate Plus", "Enter your Plus Plan Activation Key:", show='*')
        if key == "plusplan123":
            self.plus_unlocked = True
            messagebox.showinfo("Plus Activated", "Your Plus Plan has been activated!")
            self.add_calendar_tab()
        else:
            messagebox.showerror("Error", "Invalid key. Please try again.")

    def add_calendar_tab(self):
        """
        Add the Calendar tab once the Plus Plan is activated and set it up.
        """
        self.calendar_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.calendar_tab, text='Calendar')
        self.setup_calendar_tab()

    def setup_calendar_tab(self):
        """
        Set up the Calendar tab with a calendar widget, reminder fields, and a pinned reminders list.
        """
        container = ttk.Frame(self.calendar_tab)
        container.grid(row=0, column=0, sticky='nsew')
        self.calendar_tab.rowconfigure(0, weight=1)
        self.calendar_tab.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)

        left_frame = ttk.Frame(container, padding=20)
        left_frame.grid(row=0, column=0, sticky='nsew')
        left_frame.columnconfigure(0, weight=1)

        # Calendar widget for date selection
        self.cal = Calendar(left_frame, selectmode='day',
                            year=datetime.now().year,
                            month=datetime.now().month,
                            day=datetime.now().day)
        self.cal.grid(row=0, column=0, pady=10, sticky='w')

        # Reminder text entry
        ttk.Label(left_frame, text="Reminder Text:").grid(row=1, column=0, sticky='w', pady=(10,0))
        self.reminder_text = tk.StringVar()
        reminder_entry = ttk.Entry(left_frame, textvariable=self.reminder_text, width=40)
        reminder_entry.grid(row=2, column=0, pady=5, sticky='w')

        # Reminder time entry
        ttk.Label(left_frame, text="Reminder Time (HH:MM):").grid(row=3, column=0, sticky='w', pady=(10,0))
        self.reminder_time_text = tk.StringVar()
        reminder_time_entry = ttk.Entry(left_frame, textvariable=self.reminder_time_text, width=10)
        reminder_time_entry.grid(row=4, column=0, pady=5, sticky='w')

        # Add reminder button
        add_button = ttk.Button(left_frame, text="Add Reminder", command=self.add_reminder)
        add_button.grid(row=5, column=0, pady=10, sticky='w')

        left_frame.rowconfigure(6, weight=1)

        # Right frame with pinned reminders
        right_frame = ttk.Frame(container, padding=20)
        right_frame.grid(row=0, column=1, sticky='nsew')
        right_frame.rowconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)

        ttk.Label(right_frame, text="Upcoming Reminders:", font=("Helvetica", 14)).grid(row=0, column=0, pady=(0,10), sticky='w')

        # Treeview for reminders
        self.reminders_tree = ttk.Treeview(right_frame, columns=('datetime', 'reminder'), show='headings', height=15)
        self.reminders_tree.heading('datetime', text='Date/Time')
        self.reminders_tree.heading('reminder', text='Reminder')
        self.reminders_tree.column('datetime', width=150)
        self.reminders_tree.column('reminder', width=200)
        self.reminders_tree.grid(row=1, column=0, sticky='nsew')

        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.reminders_tree.yview)
        self.reminders_tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky='ns')

    def add_reminder(self):
        """
        Add a reminder based on the selected date and entered time.
        Validates that the reminder is set for a future time.
        """
        date_str = self.cal.get_date()  # "MM/DD/YYYY"
        reminder = self.reminder_text.get().strip()
        reminder_time = self.reminder_time_text.get().strip()

        if not reminder:
            messagebox.showwarning("No Text", "Please enter a reminder text.")
            return

        if not reminder_time:
            messagebox.showwarning("No Time", "Please enter a time in HH:MM format.")
            return

        # Parse the reminder time and date
        try:
            hour, minute = map(int, reminder_time.split(':'))
            month, day, year = map(int, date_str.split('/'))
            if year < 1000:
                year += 2000
            reminder_dt = datetime(year, month, day, hour, minute)
        except ValueError:
            messagebox.showerror("Invalid Time", "Please enter time in HH:MM format and select a valid date.")
            return

        now = datetime.now()
        if reminder_dt <= now:
            messagebox.showwarning("Past Time", "You cannot set a reminder in the past. Please select a future time.")
            return

        self.reminders.append((reminder_dt, reminder))
        self.reminders.sort(key=lambda x: x[0])
        self.reminder_text.set("")
        self.reminder_time_text.set("")
        messagebox.showinfo("Reminder Added", f"Reminder added for {reminder_dt.strftime('%m/%d/%Y %H:%M')}")

        self.refresh_pinned_reminders()

    def refresh_pinned_reminders(self):
        """
        Refresh the pinned reminders list, showing only upcoming reminders.
        """
        for i in self.reminders_tree.get_children():
            self.reminders_tree.delete(i)

        now = datetime.now()
        for dt, txt in self.reminders:
            if dt >= now:
                dt_str = dt.strftime('%m/%d/%Y %H:%M')
                self.reminders_tree.insert('', 'end', values=(dt_str, txt))

    def start_reminder_checker(self):
        """
        Start a background thread that periodically checks for due reminders.
        """
        t = threading.Thread(target=self.reminder_checker_thread, daemon=True)
        t.start()

    def reminder_checker_thread(self):
        """
        Background thread method that checks for reminders that are now due.
        If found, it displays a notification and removes them.
        Runs every 60 seconds.
        """
        while self.check_reminders:
            now = datetime.now()
            due_reminders = [r for r in self.reminders if r[0] <= now]

            for r in due_reminders:
                dt, txt = r
                self.root.after(0, lambda txt=txt: messagebox.showinfo("Reminder Due", f"Reminder: {txt}"))
                self.reminders.remove(r)

            self.root.after(0, self.refresh_pinned_reminders)
            time.sleep(60)

    def setup_place_order_tab(self):
        """
        Set up the Place Order tab, allowing the user to enter quantities for products and place an order.
        """
        main_frame = ttk.Frame(self.place_order_tab, padding=20)
        main_frame.grid(row=0, column=0, sticky='nsew')
        self.place_order_tab.rowconfigure(0, weight=1)
        self.place_order_tab.columnconfigure(0, weight=1)

        ttk.Label(main_frame, text="Enter Quantities for Products:", font=("Helvetica", 18)).grid(row=0, column=0, pady=10, sticky='w')

        self.product_entries = []
        products_frame = ttk.Frame(main_frame)
        products_frame.grid(row=1, column=0, pady=10, sticky='nsew')
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # Create input fields for each product
        for idx, product in enumerate(self.controller.data_store.products):
            frame = ttk.Frame(products_frame)
            frame.grid(row=idx, column=0, pady=5, sticky='w')

            label = ttk.Label(frame, text=str(product), font=("Helvetica", 14))
            label.grid(row=0, column=0, padx=5, sticky='w')

            quantity_var = tk.StringVar(value='0')
            entry = ttk.Entry(frame, textvariable=quantity_var, width=5)
            entry.grid(row=0, column=1, padx=5, sticky='e')

            self.product_entries.append((product, quantity_var))

        ttk.Label(main_frame, text="Email Address (for updates):", font=("Helvetica", 14)).grid(row=2, column=0, pady=10, sticky='w')
        self.email_var = tk.StringVar(value=self.controller.user.email or '')
        self.email_entry = ttk.Entry(main_frame, textvariable=self.email_var, font=("Helvetica", 14))
        self.email_entry.grid(row=3, column=0, pady=5, sticky='w')

        ttk.Button(main_frame, text="Place Order", command=self.place_order_with_payment).grid(row=4, column=0, pady=20)

    def place_order_with_payment(self):
        """
        Gather selected products and quantities, then initiate payment via Stripe Checkout.
        After payment is confirmed, place the order.
        """
        self.status_var.set("Initiating payment...")
        self.root.update_idletasks()

        items = []
        # Validate quantities and inventory
        for product, quantity_var in self.product_entries:
            try:
                quantity = int(quantity_var.get())
            except:
                quantity = 0
            if quantity > 0:
                if product.inventory >= quantity:
                    items.append((product, quantity))
                else:
                    messagebox.showwarning("Warning", f"Insufficient inventory for {product.name}. Available: {product.inventory}")
                    self.status_var.set("Order placement failed.")
                    return

        if not items:
            messagebox.showwarning("Warning", "No quantities entered.")
            self.status_var.set("No items to order.")
            return

        # Get email for updates
        email = self.controller.user.email or self.email_var.get().strip()
        if not email:
            email = simpledialog.askstring("Email", "Enter your email address:")
        if email:
            self.controller.user.email = email.strip()
        else:
            messagebox.showwarning("Warning", "Email address is required.")
            self.status_var.set("Order placement failed due to missing email address.")
            return

        # Map product IDs to Stripe price IDs
        price_mapping = {
            1: "price_1QWiM3IVLMb473Yf22cwdoCU",
            2: "price_1QWiMPIVLMb473YfYDw60iF5",
            3: "price_1QWiMmIVLMb473YfgBZ2TJ76",
            4: "price_1QWiNCIVLMb473YfKr1u0pwj",
            5: "price_1QWiX2IVLMb473YfnTOiuPHP",
            6: "price_1QWiXOIVLMb473YfDQT0jRfM",
            7: "price_1QWiXiIVLMb473YfcsnbLflg",
            8: "price_1QWiY1IVLMb473Yf0w1szo8Z",
            9: "price_1QWiYcIVLMb473YfCzD5xJl8",
            10: "price_1QWiYyIVLMb473YfrxDzxbnz",
            11: "price_1QWiZNIVLMb473YfJmYOhA1i",
            12: "price_1QWiZnIVLMb473YfIHLeseo3",
            13: "price_1QWia5IVLMb473YfPyKA6Q4o",
            14: "price_1QWiaQIVLMb473YfZzaWFM3j",
            15: "price_1QWiahIVLMb473YfU6NnjFjt",
        }

        line_items = []
        for product, quantity in items:
            price_id = price_mapping.get(product.product_id)
            if not price_id:
                messagebox.showerror("Error", f"No Stripe price ID for {product.name}. Cannot process payment.")
                return
            line_items.append({"price": price_id, "quantity": quantity})

        # Create Stripe Checkout Session
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url='http://localhost/success',
                cancel_url='http://localhost/cancel'
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create Stripe checkout session: {e}")
            self.status_var.set("Payment initiation failed.")
            return

        self.current_session_id = session.id
        webbrowser.open(session.url)

        # After user completes payment, they must confirm payment in the app
        confirm_frame = ttk.Frame(self.place_order_tab, padding=20)
        confirm_frame.grid(row=5, column=0, pady=20, sticky='n')
        ttk.Button(confirm_frame, text="Confirm Payment", command=lambda: self.confirm_payment(items)).grid(row=0, column=0, padx=10)

        self.status_var.set("Please complete payment in the browser and then click Confirm Payment.")

    def confirm_payment(self, items):
        """
        Confirm the payment with Stripe. If payment succeeded, place the order.
        """
        self.status_var.set("Confirming payment...")
        self.root.update_idletasks()

        try:
            session = stripe.checkout.Session.retrieve(self.current_session_id)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve session: {e}")
            self.status_var.set("Payment confirmation failed.")
            return

        if session.payment_status == "paid":
            # Payment successful, now place the order
            order_items = [OrderItem(p, q) for p, q in items]
            order = Order(self.controller.user, order_items)
            external_order_id = self.controller.api_client.place_order(order)
            order.external_order_id = external_order_id
            order.status = OrderStatus.PROCESSING
            self.controller.data_store.add_order(order)

            # Update inventory
            for p, q in items:
                p.inventory -= q
                self.controller.data_store.update_inventory(p.product_id, p.inventory)

            # Send confirmation email
            if self.controller.user.email:
                order_details = "\n".join([f"{item.product.name} (x{item.quantity})" for item in order_items])
                email_body = f"""
Thank you for your order!
Order ID: {order.order_id}
External Order ID: {external_order_id}
Items:
{order_details}

Total Price: ${order.get_total_order_price():.2f}
Status: {order.status.value}

You will receive updates on your order at this email address.
"""
                send_email(self.controller.user.email, "Order Confirmation", email_body)

            messagebox.showinfo("Success", f"Order placed successfully!\nInternal Order ID: {order.order_id}\nExternal Order ID: {external_order_id}")
            self.refresh_order_history_tab()
            for product, quantity_var in self.product_entries:
                quantity_var.set('0')
            self.status_var.set("Order placed successfully.")
        else:
            messagebox.showwarning("Warning", "Payment not completed yet. Please ensure you completed payment in the browser.")
            self.status_var.set("Payment not complete.")

    def setup_order_history_tab(self):
        """
        Set up the Order History tab, showing all past orders and providing a way to cancel orders.
        """
        main_frame = ttk.Frame(self.order_history_tab, padding=20)
        main_frame.grid(row=0, column=0, sticky='nsew')
        self.order_history_tab.rowconfigure(0, weight=1)
        self.order_history_tab.columnconfigure(0, weight=1)

        ttk.Label(main_frame, text="Your Order History:", font=("Helvetica", 18)).grid(row=0, column=0, pady=10, sticky='w')

        self.order_history_tree = ttk.Treeview(main_frame, columns=('Order ID', 'External ID', 'Items', 'Total', 'Status'), show='headings')
        self.order_history_tree.heading('Order ID', text='Order ID')
        self.order_history_tree.heading('External ID', text='External ID')
        self.order_history_tree.heading('Items', text='Items')
        self.order_history_tree.heading('Total', text='Total')
        self.order_history_tree.heading('Status', text='Status')
        self.order_history_tree.column('Order ID', width=80, anchor='center')
        self.order_history_tree.column('External ID', width=100, anchor='center')
        self.order_history_tree.column('Items', width=300, anchor='w')
        self.order_history_tree.column('Total', width=80, anchor='center')
        self.order_history_tree.column('Status', width=100, anchor='center')
        self.order_history_tree.grid(row=1, column=0, sticky='nsew')
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, pady=10, sticky='ew')
        main_frame.rowconfigure(2, weight=0)

        self.cancel_order_button = ttk.Button(buttons_frame, text="Cancel Selected Order", command=self.cancel_selected_order)
        self.cancel_order_button.grid(row=0, column=0, padx=5, sticky='w')

        self.refresh_order_history_tab()

    def refresh_order_history_tab(self):
        """
        Refresh the Order History tab to reflect the user's current orders.
        """
        for item in self.order_history_tree.get_children():
            self.order_history_tree.delete(item)

        for order in self.controller.user.order_history:
            items_str = ', '.join([str(item) for item in order.items])
            total_price = order.get_total_order_price()
            self.order_history_tree.insert('', 'end', values=(order.order_id, order.external_order_id, items_str, f"${total_price:.2f}", order.status.value))

    def cancel_selected_order(self):
        """
        Cancel the currently selected order if it is still in Processing status.
        """
        selected_item = self.order_history_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "No order selected.")
            return

        order_id = self.order_history_tree.item(selected_item, 'values')[0]
        order = self.controller.data_store.get_order_by_id(int(order_id))

        if order.status != OrderStatus.PROCESSING:
            messagebox.showinfo("Info", "Only orders with 'Processing' status can be cancelled.")
            return

        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to cancel Order {order.order_id}?")
        if confirm:
            success = self.controller.cancel_order(order)
            if success:
                messagebox.showinfo("Success", f"Order {order.order_id} has been cancelled.")
                self.refresh_order_history_tab()
            else:
                messagebox.showerror("Error", "Failed to cancel the order.")

    def setup_track_order_tab(self):
        """
        Set up the Track Order tab, allowing the user to enter an external order ID to track.
        """
        main_frame = ttk.Frame(self.track_order_tab, padding=20)
        main_frame.grid(row=0, column=0, sticky='nsew')
        self.track_order_tab.rowconfigure(0, weight=1)
        self.track_order_tab.columnconfigure(0, weight=1)

        ttk.Label(main_frame, text="Enter External Order ID:", font=("Helvetica", 16)).grid(row=0, column=0, pady=10, sticky='w')
        self.track_order_entry = ttk.Entry(main_frame, font=("Helvetica", 14))
        self.track_order_entry.grid(row=1, column=0, pady=10, sticky='w')

        ttk.Button(main_frame, text="Track Order", command=self.track_order).grid(row=2, column=0, pady=10, sticky='w')
        self.track_order_result_label = ttk.Label(main_frame, text="", justify='left', font=("Helvetica", 12))
        self.track_order_result_label.grid(row=3, column=0, pady=10, sticky='w')

    def track_order(self):
        """
        Fetch the tracking information for the given external order ID and update the UI.
        """
        self.status_var.set("Fetching tracking information...")
        self.root.update_idletasks()

        external_order_id_str = self.track_order_entry.get()
        if external_order_id_str.isdigit():
            external_order_id = int(external_order_id_str)
            order = self.controller.data_store.get_order_by_external_id(external_order_id)
            if order:
                if order.external_order_id:
                    self.update_order_status_and_map(order)
                    self.status_var.set("Tracking information updated.")
                    self.root.after(5000, lambda: self.status_var.set(""))
            else:
                self.track_order_result_label.config(text="Order not found.")
                self.status_var.set("Order not found.")
        else:
            messagebox.showwarning("Warning", "Invalid External Order ID.")
            self.status_var.set("Invalid External Order ID.")

    def update_order_status_and_map(self, order):
        """
        Update the displayed order status and show a map of the order's current location and route.
        
        Parameters:
            order (Order): The order to track.
        """
        progress = ttk.Progressbar(self.track_order_tab, mode='indeterminate')
        progress.grid(row=4, column=0, pady=10, sticky='w')
        progress.start()

        external_order_id = order.external_order_id
        new_status, location, arrival_date, coordinates, expected_arrival = self.controller.api_client.get_order_status(external_order_id)
        if new_status:
            order.update_status(new_status)
            self.controller.data_store.update_order_status(order)
        status = order.status.value
        items_str = '\n'.join([str(item) for item in order.items])
        total_price = order.get_total_order_price()
        tracking_info = (
            f"Order {order.order_id}\n"
            f"Status: {status}\n"
            f"Location: {location}\n"
            f"Expected Arrival: {expected_arrival}\n"
            f"Items:\n{items_str}\n"
            f"Total Price: ${total_price:.2f}"
        )
        self.track_order_result_label.config(text=tracking_info)

        self.show_map(external_order_id)
        self.refresh_order_history_tab()
        progress.stop()
        progress.grid_forget()

    def show_map(self, external_order_id):
        """
        Show a folium map for the given external order ID, including current location and route.
        """
        _, _, _, coordinates, expected_arrival = self.controller.api_client.get_order_status(external_order_id)

        if not coordinates or coordinates['latitude'] is None or coordinates['longitude'] is None:
            messagebox.showwarning("Warning", "Location coordinates not available.")
            return

        latitude = coordinates['latitude']
        longitude = coordinates['longitude']

        map_obj = folium.Map(location=[latitude, longitude], zoom_start=12)
        folium.Marker(
            [latitude, longitude],
            tooltip='Current Location',
            icon=folium.Icon(color='red', icon='truck', prefix='fa')
        ).add_to(map_obj)

        route_coords = self.controller.api_client.get_order_route(external_order_id)
        if route_coords:
            start_lat, start_lon = route_coords[0]
            end_lat, end_lon = route_coords[-1]
            folium.Marker(
                [start_lat, start_lon],
                tooltip='Processing Center',
                icon=folium.Icon(color='blue', icon='building', prefix='fa')
            ).add_to(map_obj)
            folium.Marker(
                [end_lat, end_lon],
                tooltip='Destination',
                icon=folium.Icon(color='green', icon='home', prefix='fa')
            ).add_to(map_obj)
            folium.PolyLine(route_coords, color="blue", weight=2.5, opacity=1).add_to(map_obj)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
            map_obj.save(tmp_file.name)
            map_path = tmp_file.name

        webbrowser.open(f'file://{map_path}')

    def setup_inventory_tab(self):
        """
        Set up the Inventory tab. If not admin authenticated, show a login prompt.
        Otherwise, show the inventory contents.
        """
        self.inventory_main_frame = ttk.Frame(self.inventory_tab, padding=20)
        self.inventory_main_frame.grid(row=0, column=0, sticky='nsew')
        self.inventory_tab.rowconfigure(0, weight=1)
        self.inventory_tab.columnconfigure(0, weight=1)

        if not self.admin_authenticated:
            self.locked_label = ttk.Label(self.inventory_main_frame, text="Admin access required.", font=("Helvetica", 16))
            self.locked_label.grid(row=0, column=0, pady=20)

            self.login_button = ttk.Button(
                self.inventory_main_frame,
                text="Enter Admin Password",
                command=self.prompt_admin_password
            )
            self.login_button.grid(row=1, column=0, pady=10)
        else:
            self.show_inventory_contents()

    def prompt_admin_password(self):
        """
        Prompt the user for the admin password. If correct, allow inventory editing.
        """
        password = simpledialog.askstring("Admin Login", "Enter admin password:", show='*')
        if password == ADMIN_PASSWORD:
            self.admin_authenticated = True
            for widget in self.inventory_main_frame.winfo_children():
                widget.destroy()
            self.show_inventory_contents()
            messagebox.showinfo("Success", "Admin access granted. You can now edit inventory levels.")
        else:
            messagebox.showerror("Error", "Incorrect password.")

    def show_inventory_contents(self):
        """
        Display the inventory contents in a treeview, allowing the admin to edit inventory by double-clicking an item.
        """
        ttk.Label(self.inventory_main_frame, text="Inventory Levels:", font=("Helvetica", 18)).grid(row=0, column=0, pady=10, sticky='w')

        self.inventory_tree = ttk.Treeview(
            self.inventory_main_frame,
            columns=('Product ID', 'Name', 'Price', 'Inventory'),
            show='headings'
        )
        self.inventory_tree.heading('Product ID', text='Product ID')
        self.inventory_tree.heading('Name', text='Name')
        self.inventory_tree.heading('Price', text='Price')
        self.inventory_tree.heading('Inventory', text='Inventory')
        self.inventory_tree.column('Product ID', width=100, anchor='center')
        self.inventory_tree.column('Name', width=200, anchor='center')
        self.inventory_tree.column('Price', width=100, anchor='center')
        self.inventory_tree.column('Inventory', width=100, anchor='center')
        self.inventory_tree.grid(row=1, column=0, sticky='nsew')

        self.inventory_main_frame.rowconfigure(1, weight=1)
        self.inventory_main_frame.columnconfigure(0, weight=1)

        self.refresh_inventory_tab()
        self.inventory_tree.bind('<Double-1>', self.on_double_click)

    def on_double_click(self, event):
        """
        Handle double-click on an inventory item to edit its inventory level.
        """
        selected_item = self.inventory_tree.selection()
        if not selected_item:
            return

        item = selected_item[0]
        values = self.inventory_tree.item(item, 'values')
        product_id = int(values[0])
        product_name = values[1]
        current_inventory = int(values[3])

        new_inventory = simpledialog.askinteger("Edit Inventory", f"Enter new inventory for '{product_name}':", initialvalue=current_inventory, minvalue=0)

        if new_inventory is not None:
            success = self.controller.data_store.update_inventory(product_id, new_inventory)
            if success:
                self.inventory_tree.set(item, 'Inventory', new_inventory)
                messagebox.showinfo("Success", f"Inventory for '{product_name}' updated to {new_inventory}.")
            else:
                messagebox.showerror("Error", f"Failed to update inventory for '{product_name}'.")

    def refresh_inventory_tab(self):
        """
        Refresh the inventory tree to show current product inventory levels.
        """
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)

        for product in self.controller.data_store.products:
            self.inventory_tree.insert('', 'end', values=(product.product_id, product.name, f"${product.price:.2f}", product.inventory))

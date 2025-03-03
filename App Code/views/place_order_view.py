# views/place_order_view.py

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from models.order import Order
from models.order_item import OrderItem
from models.order_status import OrderStatus

class PlaceOrderView:
    def __init__(self, root, controller):
        """
        A popup window to place an order by entering quantities for available products.
        
        Parameters:
            root: The root Tkinter window.
            controller: The AppController instance for accessing products and placing orders.
        """
        self.top = tk.Toplevel(root)
        self.top.title("Place Order")
        self.controller = controller

        self.top.geometry("600x400")
        self.top.grab_set()  # Modal dialog

        main_frame = ttk.Frame(self.top, padding=20)
        main_frame.pack(fill='both', expand=True)

        ttk.Label(main_frame, text="Enter Quantities for Products:", font=("Helvetica", 18)).pack(pady=10)

        self.product_entries = []

        products_frame = ttk.Frame(main_frame)
        products_frame.pack(pady=10)

        # Create an entry for each product to specify quantity
        for product in self.controller.data_store.products:
            frame = ttk.Frame(products_frame)
            frame.pack(anchor='w', pady=5)

            label = ttk.Label(frame, text=str(product), font=("Helvetica", 14))
            label.pack(side='left', padx=5)

            quantity_var = tk.IntVar(value=0)
            entry = ttk.Entry(frame, textvariable=quantity_var, width=5)
            entry.pack(side='left', padx=5)

            self.product_entries.append((product, quantity_var))

        ttk.Button(main_frame, text="Place Order", command=self.place_order).pack(pady=20)

    def place_order(self):
        """
        Collect product quantities and place the order if valid.
        """
        items = []
        for product, quantity_var in self.product_entries:
            quantity = quantity_var.get()
            if quantity > 0:
                items.append(OrderItem(product, quantity))

        if items:
            order = Order(self.controller.user, items)
            external_order_id = self.controller.api_client.place_order(order)
            order.external_order_id = external_order_id
            order.status = OrderStatus.PROCESSING
            self.controller.user.place_order(order)
            self.controller.data_store.add_order(order)
            messagebox.showinfo(
                "Success",
                f"Order placed successfully!\nInternal Order ID: {order.order_id}\nExternal Order ID: {external_order_id}"
            )
            self.top.destroy()
        else:
            messagebox.showwarning("Warning", "No quantities entered.")

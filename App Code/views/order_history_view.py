# views/order_history_view.py

import tkinter as tk
from tkinter import ttk

class OrderHistoryView:
    def __init__(self, root, controller):
        """
        A separate window to display the user's order history.
        
        Parameters:
            root: The root Tkinter window.
            controller: The AppController instance for accessing user/order data.
        """
        self.top = tk.Toplevel(root)
        self.top.title("Order History")
        self.controller = controller

        self.top.geometry("800x600")
        self.top.grab_set()

        main_frame = ttk.Frame(self.top, padding=20)
        main_frame.pack(fill='both', expand=True)

        ttk.Label(main_frame, text="Your Order History:", font=("Helvetica", 18)).pack(pady=10)

        self.tree = ttk.Treeview(main_frame, columns=('Order ID', 'External ID', 'Items', 'Total', 'Status'), show='headings')
        self.tree.heading('Order ID', text='Order ID')
        self.tree.heading('External ID', text='External ID')
        self.tree.heading('Items', text='Items')
        self.tree.heading('Total', text='Total')
        self.tree.heading('Status', text='Status')
        self.tree.column('Order ID', width=80)
        self.tree.column('External ID', width=100)
        self.tree.column('Items', width=300)
        self.tree.column('Total', width=80)
        self.tree.column('Status', width=100)
        self.tree.pack(fill='both', expand=True)

        self.refresh_order_history()

    def refresh_order_history(self):
        """
        Load the order history from the controller's user and display it in the treeview.
        """
        # Clear existing entries
        for item in self.tree.get_children():
            self.tree.delete(item)

        for order in self.controller.user.order_history:
            items_str = ', '.join([str(item) for item in order.items])
            total_price = order.get_total_order_price()
            self.tree.insert('', 'end', values=(
                order.order_id,
                order.external_order_id,
                items_str,
                f"${total_price:.2f}",
                order.status.value
            ))

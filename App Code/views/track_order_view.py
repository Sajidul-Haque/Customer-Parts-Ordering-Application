# views/track_order_view.py

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkhtmlview import HTMLLabel
import folium
import os
import threading

class TrackOrderView:
    def __init__(self, root, controller):
        """
        A popup window to track an order using its external order ID.
        
        Parameters:
            root: The root Tkinter window.
            controller: The AppController instance to retrieve and track orders.
        """
        self.top = tk.Toplevel(root)
        self.top.title("Track Order")
        self.controller = controller

        self.top.geometry("800x600")
        self.top.grab_set()

        main_frame = ttk.Frame(self.top, padding=20)
        main_frame.pack(fill='both', expand=True)

        ttk.Label(main_frame, text="Enter External Order ID:", font=("Helvetica", 16)).pack(pady=10)
        self.order_id_entry = ttk.Entry(main_frame, font=("Helvetica", 14))
        self.order_id_entry.pack(pady=10)

        ttk.Button(main_frame, text="Track Order", command=self.track_order).pack(pady=10)

        # Frame to hold the map
        self.map_frame = ttk.Frame(main_frame)
        self.map_frame.pack(fill='both', expand=True)

    def track_order(self):
        """
        Validate the external order ID and initiate tracking in a separate thread.
        """
        external_order_id_str = self.order_id_entry.get()
        if external_order_id_str.isdigit():
            external_order_id = int(external_order_id_str)
            order = self.controller.data_store.get_order_by_external_id(external_order_id)
            if order:
                if order.external_order_id:
                    # Update status and map in a separate thread
                    threading.Thread(target=self.update_order_status_and_map, args=(order,), daemon=True).start()
            else:
                messagebox.showwarning("Warning", "Order not found.")
        else:
            messagebox.showwarning("Warning", "Invalid External Order ID.")

    def update_order_status_and_map(self, order):
        """
        Retrieve the latest order status and coordinates, then display them on a map if available.
        """
        new_status, location, arrival_date, coordinates = self.controller.api_client.get_order_status(order.external_order_id)
        if new_status:
            order.update_status(new_status)
        status = order.status.value

        # Show map if coordinates are available
        if coordinates['latitude'] is not None and coordinates['longitude'] is not None:
            self.show_map(coordinates['latitude'], coordinates['longitude'], location)
        else:
            messagebox.showwarning("Warning", "Location coordinates not available.")

    def show_map(self, latitude, longitude, location_name):
        """
        Generate and display a folium map with the given coordinates and location name.
        
        Parameters:
            latitude (float): The latitude for the map marker.
            longitude (float): The longitude for the map marker.
            location_name (str): A label for the map marker tooltip.
        """
        map_obj = folium.Map(location=[latitude, longitude], zoom_start=6)
        folium.Marker([latitude, longitude], tooltip=location_name).add_to(map_obj)

        # Save and display the map
        map_html = 'order_map.html'
        map_obj.save(map_html)

        with open(map_html, 'r', encoding='utf-8') as f:
            html_content = f.read()

        self.display_map(html_content)
        os.remove(map_html)

    def display_map(self, html_content):
        """
        Display the HTML map content in the map_frame.
        
        Parameters:
            html_content (str): The HTML string of the map to display.
        """
        for widget in self.map_frame.winfo_children():
            widget.destroy()

        html_label = HTMLLabel(self.map_frame, html=html_content)
        html_label.pack(fill='both', expand=True)

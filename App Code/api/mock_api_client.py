# api/mock_api_client.py

import random
import threading
import time
from models.order_status import OrderStatus
from geopy.geocoders import Nominatim
import openrouteservice
from utils.email_util import send_email
from dotenv import load_dotenv
import os

# Replace with your actual OpenRouteService API key
ORS_API_KEY = os.getenv('ORS_API_KEY')

def geocode_address(address):
    geolocator = Nominatim(user_agent="order_tracker_app")
    location = geolocator.geocode(address)
    if location:
        return (location.latitude, location.longitude)
    else:
        raise ValueError(f"Could not geocode address: {address}")

def get_route_coordinates(start_coords, end_coords):
    client = openrouteservice.Client(key=ORS_API_KEY)
    try:
        route = client.directions(
            coordinates=[(start_coords[1], start_coords[0]), (end_coords[1], end_coords[0])],
            profile='driving-car',
            format='geojson'
        )
    except openrouteservice.exceptions.ApiError as e:
        print(f"OpenRouteService API error: {e}")
        return []

    geometry = route['features'][0]['geometry']
    route_coords = geometry['coordinates']
    # Convert coordinates from (lon, lat) to (lat, lon)
    route_coords = [(coord[1], coord[0]) for coord in route_coords]
    return route_coords

class MockAPIClient:
    def __init__(self, data_store):
        self.data_store = data_store  # Reference to DataStore
        self.external_order_statuses = {}
        self.order_lock = threading.Lock()
        self.order_updates = {}  # Stores location and arrival date
        self.location_coordinates = {}  # Stores latitude and longitude
        self.order_routes = {}  # Stores the route coordinates for each order

    def place_order(self, order):
        # Simulate sending order data to the external API
        external_order_id = random.randint(100000, 999999)
        with self.order_lock:
            self.external_order_statuses[external_order_id] = OrderStatus.PROCESSING
            # Initialize tracking info
            self.order_updates[external_order_id] = {
                'location': 'Processing Center',
                'arrival_date': 'TBD',
                'expected_arrival': 'Calculating...'
            }
            # Initialize location coordinates (e.g., warehouse location)
            self.location_coordinates[external_order_id] = {
                'latitude': None,
                'longitude': None
            }

        # Start a background thread to update status
        threading.Thread(target=self.simulate_status_updates, args=(external_order_id, order), daemon=True).start()
        return external_order_id

    def simulate_status_updates(self, external_order_id, order):
        # Example status updates
        statuses = [OrderStatus.IN_TRANSIT, OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED]

        for status in statuses:
            time.sleep(30)  # Simulate time delay
            with self.order_lock:
                self.external_order_statuses[external_order_id] = status
                order.update_status(status)

            # Send email notification
            if order.user.email:
                email_body = f"""
                Update on your order!
                Order ID: {order.order_id}
                External Order ID: {external_order_id}

                Current Status: {status.value}
                """
                send_email(order.user.email, "Order Status Update", email_body)

            # Addresses
            source_address = "3000 E Grand Blvd, Detroit, MI 48202"
            destination_address = "14601 E 12 Mile Rd, Warren, MI 48088"

            # Geocode addresses
            try:
                start_coords = geocode_address(source_address)
                end_coords = geocode_address(destination_address)
            except ValueError as ve:
                print(ve)
                continue  # Skip this iteration if geocoding fails

            # Use OpenRouteService to get the route
            route_coords = get_route_coordinates(start_coords, end_coords)
            if not route_coords:
                # Handle error if route_coords is empty
                print("Error obtaining route coordinates.")
                return

            # Store route for later use
            self.order_routes[external_order_id] = route_coords

            # Set initial location to processing center before processing time
            total_delivery_time = self.calculate_delivery_time(order)
            expected_arrival_timestamp = time.time() + 30 + total_delivery_time  # Processing time + delivery time
            with self.order_lock:
                self.location_coordinates[external_order_id]['latitude'] = start_coords[0]
                self.location_coordinates[external_order_id]['longitude'] = start_coords[1]
                self.external_order_statuses[external_order_id] = OrderStatus.PROCESSING
                self.order_updates[external_order_id]['location'] = 'Processing Center'
                self.order_updates[external_order_id]['expected_arrival'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expected_arrival_timestamp))

            # --- Processing Stage ---
            processing_time = 30  # 30 seconds
            time.sleep(processing_time)

            # Update status to IN_TRANSIT after processing
            with self.order_lock:
                self.external_order_statuses[external_order_id] = OrderStatus.IN_TRANSIT
                self.order_updates[external_order_id]['location'] = 'In Transit'

            # --- Delivery Stage ---
            # Simulate movement along the route
            total_steps = len(route_coords)
            duration_in_seconds = total_delivery_time
            interval = duration_in_seconds / total_steps

            halfway_email_sent = False

            for idx, (latitude, longitude) in enumerate(route_coords):
                time.sleep(interval)  # Wait for the interval
                with self.order_lock:
                    self.location_coordinates[external_order_id]['latitude'] = latitude
                    self.location_coordinates[external_order_id]['longitude'] = longitude

                    # Update status based on progress
                    progress = idx / total_steps
                    if progress < 0.75:
                        self.external_order_statuses[external_order_id] = OrderStatus.IN_TRANSIT
                        self.order_updates[external_order_id]['location'] = 'In Transit'
                    else:
                        self.external_order_statuses[external_order_id] = OrderStatus.OUT_FOR_DELIVERY
                        self.order_updates[external_order_id]['location'] = 'Out for Delivery'

                # Send email when halfway
                if not halfway_email_sent and progress >= 0.5:
                    if order.user.email:
                        send_email(order.user.email, f"Order {external_order_id} Update", f"Your order {external_order_id} is halfway to the destination.")
                    halfway_email_sent = True

            # Final status update
            with self.order_lock:
                self.external_order_statuses[external_order_id] = OrderStatus.DELIVERED
                self.order_updates[external_order_id]['location'] = 'Delivered'
                self.order_updates[external_order_id]['arrival_date'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                self.location_coordinates[external_order_id]['latitude'] = end_coords[0]
                self.location_coordinates[external_order_id]['longitude'] = end_coords[1]

            # Send email notification for delivery
            if order.user.email:
                send_email(order.user.email, f"Order {external_order_id} Delivered", f"Your order {external_order_id} has been delivered.")

    def calculate_delivery_time(self, order):
        # Base time in seconds (10 minutes)
        base_time = 10 * 60
        # Maximum additional time (10 minutes)
        max_additional_time = 10 * 60
        # Total number of items
        total_items = sum(item.quantity for item in order.items)
        # Total cost of items
        total_cost = sum(item.product.price * item.quantity for item in order.items)
        # Calculate additional time based on total items and total cost
        item_weight = 0.5
        cost_weight = 0.5
        # Normalize total_items and total_cost to a scale (e.g., between 0 and 1)
        max_items = 10  # Assume maximum expected items
        max_cost = 1000  # Assume maximum expected cost
        normalized_items = min(total_items / max_items, 1.0)
        normalized_cost = min(total_cost / max_cost, 1.0)
        # Calculate additional time
        additional_time = max_additional_time * (item_weight * normalized_items + cost_weight * normalized_cost)
        # Ensure total delivery time is between 10 and 20 minutes
        total_delivery_time = base_time + additional_time
        return total_delivery_time

    def get_order_status(self, external_order_id):
        with self.order_lock:
            status = self.external_order_statuses.get(external_order_id, None)
            tracking_info = self.order_updates.get(external_order_id, {
                'location': 'Unknown',
                'arrival_date': 'Unknown',
                'expected_arrival': 'Unknown'
            })
            coordinates = self.location_coordinates.get(external_order_id, {
                'latitude': None,
                'longitude': None
            })
        return status, tracking_info['location'], tracking_info['arrival_date'], coordinates, tracking_info.get('expected_arrival', 'Unknown')

    def get_order_route(self, external_order_id):
        with self.order_lock:
            return self.order_routes.get(external_order_id, None)

    def cancel_order(self, external_order_id):
        with self.order_lock:
            status = self.external_order_statuses.get(external_order_id)
            if status == OrderStatus.PROCESSING:
                self.external_order_statuses[external_order_id] = OrderStatus.CANCELLED
                # Optionally, send an email notification about the cancellation
                order = self.get_order_by_external_id(external_order_id)
                if order and order.user.email:
                    email_body = f"""
                    Your order {external_order_id} has been cancelled successfully.
                    """
                    send_email(order.user.email, "Order Cancellation", email_body)
                return True
            else:
                return False

    def get_order_by_external_id(self, external_order_id):
        # Retrieve the order from DataStore using external_order_id
        return self.data_store.get_order_by_external_id(external_order_id)

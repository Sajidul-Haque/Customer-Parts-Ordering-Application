# models/data_store.py

import sqlite3
from models.product import Product
from models.order_item import OrderItem
from models.order import Order
from models.order_status import OrderStatus
from models.user import User
import logging

class DataStore:
    def __init__(self, user):
        """
        Initialize the DataStore, connecting to the SQLite database.
        Loads products and orders from the database into memory.
        
        Parameters:
            user (User): The user instance associated with this data store.
        """
        self.user = user
        self.products = []  # List of Product instances
        self.orders = []    # List of Order instances

        # Connect to the SQLite database
        self.conn = sqlite3.connect('data_store.db')
        self.create_tables()
        self.load_products()
        self.load_orders()

    def create_tables(self):
        """
        Create the necessary tables (orders, products) in the SQLite database if they don't exist.
        """
        cursor = self.conn.cursor()
        # Create orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                items TEXT,
                total_price REAL,
                status TEXT,
                external_order_id INTEGER
            )
        ''')

        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                inventory INTEGER NOT NULL
            )
        ''')

        self.conn.commit()

    def add_order(self, order):
        """
        Add an order to the database and in-memory lists.
        
        Parameters:
            order (Order): The Order instance to add.
        """
        self.orders.append(order)
        self.user.place_order(order)  # Add to user's order history

        # Save to database
        cursor = self.conn.cursor()
        items_str = ';'.join([f"{item.product.product_id},{item.quantity}" for item in order.items])
        cursor.execute('''
            INSERT INTO orders (user, items, total_price, status, external_order_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            order.user.username,
            items_str,
            order.get_total_order_price(),
            order.status.value,
            order.external_order_id
        ))
        self.conn.commit()
        order.order_id = cursor.lastrowid  # Assign the auto-generated order_id

    def load_orders(self):
        """
        Load all orders from the database that belong to the current user into memory.
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT order_id, user, items, total_price, status, external_order_id FROM orders')
        rows = cursor.fetchall()
        for row in rows:
            order_id, username, items_str, total_price, status_str, external_order_id = row

            # Only load orders for the current user
            if username != self.user.username:
                continue

            items = []
            for item_str in items_str.split(';'):
                if item_str:
                    try:
                        product_id_str, quantity_str = item_str.split(',')
                        product = self.get_product_by_id(int(product_id_str))
                        if product:
                            items.append(OrderItem(product, int(quantity_str)))
                    except ValueError:
                        print(f"Invalid item format: {item_str}")
                        continue

            # Create Order instance
            order = Order(self.user, items)
            order.order_id = order_id
            order.external_order_id = external_order_id
            order.status = OrderStatus(status_str)
            self.orders.append(order)
            self.user.place_order(order)

    def get_order_by_id(self, order_id):
        """
        Retrieve an order by its internal order ID.
        
        Parameters:
            order_id (int): The internal order ID to search for.
            
        Returns:
            The matching Order instance or None if not found.
        """
        for order in self.orders:
            if order.order_id == order_id:
                return order
        return None

    def get_order_by_external_id(self, external_order_id):
        """
        Retrieve an order by its external order ID.
        
        Parameters:
            external_order_id (int): The external order ID to search for.
            
        Returns:
            The matching Order instance or None if not found.
        """
        for order in self.orders:
            if order.external_order_id == external_order_id:
                return order
        return None

    def load_products(self):
        """
        Load products from the database. If none exist, insert predefined products first.
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT product_id, name, price, inventory FROM products')
        rows = cursor.fetchall()
        if not rows:
            # Insert predefined products if none exist
            self.insert_predefined_products()
            cursor.execute('SELECT product_id, name, price, inventory FROM products')
            rows = cursor.fetchall()

        self.products = [
            Product(product_id=row[0], name=row[1], price=row[2], inventory=row[3])
            for row in rows
        ]

    def insert_predefined_products(self):
        """
        Insert a predefined set of products into the database.
        This is run if no products currently exist.
        """
        cursor = self.conn.cursor()
        predefined_products = [
            ("Brake Pads", 29.99, 100),
            ("Oil Filter", 9.99, 200),
            ("Spark Plug", 4.99, 150),
            ("Air Filter", 19.99, 120),
            ("Headlight Bulb", 14.99, 80),
            ("Fuel Pump", 89.99, 60),
            ("Alternator", 149.99, 40),
            ("Battery", 119.99, 50),
            ("Radiator", 199.99, 30),
            ("Clutch Kit", 249.99, 20),
            ("Brake Disc", 39.99, 90),
            ("Suspension Spring", 59.99, 70),
            ("Shock Absorber", 79.99, 65),
            ("Catalytic Converter", 299.99, 25),
            ("Muffler", 99.99, 55),
        ]
        cursor.executemany('''
            INSERT INTO products (name, price, inventory) VALUES (?, ?, ?)
        ''', predefined_products)
        self.conn.commit()
        logging.info("Inserted predefined products into the database.")

    def get_product_by_id(self, product_id):
        """
        Retrieve a product by its product_id.
        
        Parameters:
            product_id (int): The ID of the product to search for.
            
        Returns:
            The matching Product instance or None if not found.
        """
        for product in self.products:
            if product.product_id == product_id:
                return product
        return None

    def update_order_status(self, order):
        """
        Update the status of an order both in-memory and in the database.
        
        Parameters:
            order (Order): The order whose status is to be updated.
        """
        # Update in-memory list
        for idx, existing_order in enumerate(self.orders):
            if existing_order.order_id == order.order_id:
                self.orders[idx] = order
                break
        # Update user's order history
        for idx, existing_order in enumerate(self.user.order_history):
            if existing_order.order_id == order.order_id:
                self.user.order_history[idx] = order
                break

        # Update in database
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE orders SET status=? WHERE order_id=?
        ''', (order.status.value, order.order_id))
        self.conn.commit()

    def update_inventory(self, product_id, new_inventory):
        """
        Update the inventory of a product in the database and in-memory.
        
        Parameters:
            product_id (int): The ID of the product to update.
            new_inventory (int): The new inventory quantity.
            
        Returns:
            bool: True if inventory updated successfully, False otherwise.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE products SET inventory = ? WHERE product_id = ?
            ''', (new_inventory, product_id))
            self.conn.commit()

            # Update in-memory product list
            for product in self.products:
                if product.product_id == product_id:
                    product.inventory = new_inventory
                    break

            logging.info(f"Updated inventory for Product ID {product_id} to {new_inventory}.")
            return True
        except sqlite3.Error as e:
            logging.error(f"Failed to update inventory for Product ID {product_id}: {e}")
            return False

    def close_connection(self):
        """
        Close the database connection when the application is shutting down.
        """
        try:
            self.conn.close()
            logging.info("Database connection closed.")
        except sqlite3.Error as e:
            logging.error(f"Failed to close database connection: {e}")

# models/product.py

class Product:
    def __init__(self, product_id, name, price, inventory=0):
        """
        Represent a single product with ID, name, price, and available inventory.
        
        Parameters:
            product_id (int): The unique ID of the product.
            name (str): The product name.
            price (float): The product price.
            inventory (int): How many of this product are in stock.
        """
        self.product_id = product_id
        self.name = name
        self.price = price
        self.inventory = inventory

    def __repr__(self):
        """
        String representation of the product for debugging or logging.
        
        Returns:
            str: Formatted string with product name and price.
        """
        return f"{self.name} (${self.price})"

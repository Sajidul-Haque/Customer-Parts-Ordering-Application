# models/order_item.py

class OrderItem:
    def __init__(self, product, quantity):
        """
        Represent a single item in an order, with a product and a quantity.
        
        Parameters:
            product (Product): The product associated with this order item.
            quantity (int): The quantity of the product in this order item.
        """
        self.product = product
        self.quantity = quantity

    def get_total_price(self):
        """
        Calculate the total price for this order item: product price * quantity.
        
        Returns:
            float: The total price for this item.
        """
        return self.product.price * self.quantity

    def __str__(self):
        """
        String representation for printing or logging this order item.
        
        Returns:
            str: A formatted string showing product name, quantity, and total price.
        """
        return f"{self.product.name} x{self.quantity} (${self.get_total_price():.2f})"

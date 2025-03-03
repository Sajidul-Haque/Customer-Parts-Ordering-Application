# models/order.py

from models.order_status import OrderStatus

class Order:
    def __init__(self, user, items):
        """
        Represent a single order placed by a user.
        
        Parameters:
            user (User): The user who placed the order.
            items (list of OrderItem): The items included in this order.
        """
        self.user = user
        self.items = items
        self.order_id = self.generate_order_id()
        self.status = OrderStatus.PROCESSING
        self.external_order_id = None  # Set when placed via external API

    def generate_order_id(self):
        """
        Generate a random internal order ID.
        
        Returns:
            int: A random integer used as the internal order ID.
        """
        import random
        return random.randint(1000, 9999)

    def update_status(self, new_status):
        """
        Update the status of the order.
        
        Parameters:
            new_status (OrderStatus): The new status to apply to this order.
        """
        self.status = new_status

    def get_total_order_price(self):
        """
        Calculate the total price of the entire order.
        
        Returns:
            float: The sum of the total prices of all order items.
        """
        return sum(item.get_total_price() for item in self.items)

    def cancel_order(self):
        """
        Attempt to cancel the order if it is still in Processing status.
        
        Returns:
            bool: True if order was cancelled, False otherwise.
        """
        if self.status == OrderStatus.PROCESSING:
            self.status = OrderStatus.CANCELLED
            return True
        return False

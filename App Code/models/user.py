# models/user.py

class User:
    def __init__(self, username, email=None):
        """
        Represent a user of the system with a username and an optional email.
        
        Parameters:
            username (str): The user's username.
            email (str, optional): The user's email address.
        """
        self.username = username
        self.email = email
        self.order_history = []

    def place_order(self, order):
        """
        Add an order to the user's order history.
        
        Parameters:
            order (Order): The order to add to the user's history.
        """
        self.order_history.append(order)

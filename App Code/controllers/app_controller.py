# controllers/app_controller.py

from api.mock_api_client import MockAPIClient
from models.data_store import DataStore
from models.user import User
from models.order_status import OrderStatus

class AppController:
    def __init__(self, root):
        """
        Initialize the application controller.
        This sets up a User, DataStore, and MockAPIClient instances.
        
        Parameters:
            root: The root Tkinter window or main application context.
        """
        # Initialize User with username and email
        self.user = User(username="ejgerg1", email="ejgerg1@gmail.com")

        # Initialize DataStore with the User instance (handles database and data management)
        self.data_store = DataStore(self.user)

        # Initialize MockAPIClient with the DataStore instance (handles simulated external API calls)
        self.api_client = MockAPIClient(self.data_store)

    def get_order_by_external_id(self, external_order_id):
        """
        Retrieve an order by its external order ID from the data store.
        
        Parameters:
            external_order_id (int): The external order ID to search for.
            
        Returns:
            The matching Order object or None if not found.
        """
        return self.data_store.get_order_by_external_id(external_order_id)

    def cancel_order(self, order):
        """
        Attempt to cancel an existing order if it is still in 'Processing' status.
        
        Parameters:
            order (Order): The Order instance to cancel.
            
        Returns:
            bool: True if the order was successfully cancelled, False otherwise.
        """
        success = self.api_client.cancel_order(order.external_order_id)
        if success:
            order.status = OrderStatus.CANCELLED
            self.data_store.update_order_status(order)
        return success

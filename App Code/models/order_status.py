# models/order_status.py

from enum import Enum

class OrderStatus(Enum):
    """
    Enumeration of possible order statuses throughout its lifecycle.
    """
    PROCESSING = 'Processing'
    SHIPPED = 'Shipped'
    IN_TRANSIT = 'In Transit'
    OUT_FOR_DELIVERY = 'Out for Delivery'
    DELIVERED = 'Delivered'
    CANCELLED = 'Cancelled'

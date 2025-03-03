# utils/resource_path.py

import sys
import os

def resource_path(relative_path):
    """
    Get the absolute path to a resource, works for development and PyInstaller builds.
    
    Parameters:
        relative_path (str): The relative path to the resource.
    
    Returns:
        str: The absolute path to the resource.
    """
    try:
        # If running with PyInstaller, it stores resources in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# app.py

import tkinter as tk
from tkinter import ttk, messagebox
from controllers.app_controller import AppController
from views.main_view import MainView
import pystray
from PIL import Image, ImageTk
import threading

def main():
    """
    Entry point for the application.
    Initializes the main Tk window, the app controller, and the main view.
    Sets up system tray minimization behavior.
    """
    root = tk.Tk()
    root.title("ForestView Customer Tracker")
    root.state('zoomed')

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TFrame', background='#f0f4f8')
    style.configure('TNotebook', background='#003366')
    style.configure('TNotebook.Tab', font=('Helvetica', 12, 'bold'), padding=[10, 5])
    style.map('TNotebook.Tab', background=[('selected', '#0055a4')], foreground=[('selected', 'white')])

    # Initialize the controller
    app = AppController(root)

    # Instantiate MainView
    view = MainView(root, app)

    def on_quit(icon, item):
        """
        Callback to handle quitting from the system tray menu.
        Closes database connection and destroys the main window.
        """
        icon.stop()
        app.data_store.close_connection()
        root.destroy()

    def create_image():
        """
        Create an icon image for the system tray.
        
        Returns:
            PIL.Image: A solid colored image used as a tray icon.
        """
        image = Image.new('RGB', (64, 64), color=(0, 51, 102))
        return image

    icon = pystray.Icon("ForestView", create_image(), "ForestView Customer Tracker", menu=pystray.Menu(
        pystray.MenuItem("Open", lambda icon, item: show_window(icon, item)),
        pystray.MenuItem("Quit", on_quit)
    ))

    def show_window(icon, item):
        """
        Restore the main window from the system tray.
        """
        icon.stop()
        root.after(0, root.deiconify)

    def hide_window():
        """
        Minimize the application to the system tray instead of closing it.
        """
        root.withdraw()
        icon.run_detached()

    # Override the close window protocol to minimize to tray
    root.protocol("WM_DELETE_WINDOW", hide_window)

    # Start Tkinter main loop
    root.mainloop()

if __name__ == '__main__':
    main()

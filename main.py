"""
Main entry point for Liquidación OPAEF application.
"""
import sys
from src.gui.main_window import MainWindow


def main():
    """Launch the application."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()

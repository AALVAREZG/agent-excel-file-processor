"""
Custom information dialog with improved readability and formatting.
"""
import customtkinter as ctk
from tkinter import Text, Scrollbar
import tkinter as tk


class InfoDialog(ctk.CTkToplevel):
    """
    Custom information dialog with better formatting and readability.
    """

    def __init__(self, parent, title: str, content: str):
        """
        Create an information dialog.

        Args:
            parent: Parent window
            title: Dialog title
            content: Information content (can include formatting markers)
        """
        super().__init__(parent)

        # Configure window
        self.title(title)
        self.geometry("700x600")
        self.resizable(True, True)

        # Center on parent
        self.transient(parent)
        self.grab_set()

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Title bar
        title_frame = ctk.CTkFrame(self, fg_color="#1976D2", corner_radius=0)
        title_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)

        title_label = ctk.CTkLabel(
            title_frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        title_label.pack(pady=15, padx=20)

        # Content frame with scrollbar
        content_frame = ctk.CTkFrame(self, fg_color="white")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Create text widget for content (allows better formatting)
        self.text_widget = Text(
            content_frame,
            wrap="word",
            font=("Segoe UI", 11),
            bg="white",
            fg="#2E3440",
            padx=20,
            pady=20,
            relief="flat",
            cursor="arrow"
        )
        self.text_widget.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        scrollbar = Scrollbar(content_frame, command=self.text_widget.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text_widget.config(yscrollcommand=scrollbar.set)

        # Configure text tags for formatting
        self.text_widget.tag_configure("section_header",
                                       font=("Segoe UI", 13, "bold"),
                                       foreground="#1976D2",
                                       spacing1=15,
                                       spacing3=8)

        self.text_widget.tag_configure("subsection_header",
                                       font=("Segoe UI", 11, "bold"),
                                       foreground="#424242",
                                       spacing1=10,
                                       spacing3=5)

        self.text_widget.tag_configure("bullet",
                                       lmargin1=20,
                                       lmargin2=35,
                                       spacing1=3)

        self.text_widget.tag_configure("normal",
                                       lmargin1=20,
                                       lmargin2=20,
                                       spacing1=2)

        # Parse and insert formatted content
        self._insert_formatted_content(content)

        # Make text read-only
        self.text_widget.config(state="disabled")

        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=15)

        close_button = ctk.CTkButton(
            button_frame,
            text="Cerrar",
            command=self.destroy,
            width=100,
            height=32,
            fg_color="#1976D2",
            hover_color="#1565C0"
        )
        close_button.pack(side="right")

        # Focus on close button
        close_button.focus()

        # Bind Escape key
        self.bind("<Escape>", lambda e: self.destroy())

    def _insert_formatted_content(self, content: str):
        """Parse and insert formatted content into text widget."""
        self.text_widget.config(state="normal")

        lines = content.split('\n')

        for line in lines:
            line_stripped = line.strip()

            if not line_stripped:
                # Empty line for spacing
                self.text_widget.insert("end", "\n")
                continue

            # Section headers (all caps, ends with :)
            if line_stripped.isupper() and line_stripped.endswith(':'):
                self.text_widget.insert("end", line_stripped + "\n", "section_header")

            # Subsection headers (numbered like "1. SOMETHING:")
            elif line_stripped[0].isdigit() and '.' in line_stripped[:3] and line_stripped.endswith(':'):
                self.text_widget.insert("end", line_stripped + "\n", "subsection_header")

            # Bullet points (start with •)
            elif line_stripped.startswith('•'):
                # Remove bullet and add custom formatting
                text = line_stripped[1:].strip()
                self.text_widget.insert("end", "  •  " + text + "\n", "bullet")

            # Normal text
            else:
                self.text_widget.insert("end", line_stripped + "\n", "normal")

        self.text_widget.config(state="disabled")

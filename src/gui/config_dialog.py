"""
Configuration dialog for application settings.
"""
import customtkinter as ctk
from tkinter import messagebox, ttk
import tkinter as tk
from typing import Optional, Callable, Dict, List

from src.models.grouping_config import GroupingConfig, ConceptGroup, AppearanceConfig
from src.models.liquidation import TributeRecord


class ConfigDialog(ctk.CTkToplevel):
    """Modal dialog for configuring application settings."""

    def __init__(self, parent, grouping_config: GroupingConfig,
                 appearance_config: AppearanceConfig,
                 on_save: Callable[[GroupingConfig, AppearanceConfig], None],
                 current_records: Optional[List[TributeRecord]] = None):
        """
        Initialize configuration dialog.

        Args:
            parent: Parent window
            grouping_config: Current grouping configuration
            appearance_config: Current appearance configuration
            on_save: Callback function to save configurations
            current_records: Current loaded tribute records for concept selection
        """
        super().__init__(parent)

        self.grouping_config = grouping_config
        self.appearance_config = appearance_config
        self.on_save = on_save
        self.current_records = current_records or []

        # Current selected section
        self.current_section = "grouping"

        # Window setup
        self.title("Configuración de la Aplicación")
        self.geometry("900x700")

        # Make it modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left sidebar for navigation
        self._create_sidebar()

        # Right content area
        self._create_content_area()

        # Button bar at bottom
        self._create_button_bar()

    def _create_sidebar(self):
        """Create left sidebar with navigation."""
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0,
                                    fg_color=("#e0e0e0", "#2b2b2b"))
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_propagate(False)

        # Title
        title_label = ctk.CTkLabel(
            self.sidebar,
            text="Configuración",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(20, 30), padx=15)

        # Navigation buttons
        self.nav_buttons = {}

        # Grouping section
        self.nav_buttons["grouping"] = ctk.CTkButton(
            self.sidebar,
            text="⚙ Agrupación",
            command=lambda: self._switch_section("grouping"),
            height=40,
            fg_color="transparent",
            hover_color=("#c0c0c0", "#404040"),
            anchor="w",
            font=ctk.CTkFont(size=13)
        )
        self.nav_buttons["grouping"].pack(fill="x", padx=10, pady=5)

        # Appearance section
        self.nav_buttons["appearance"] = ctk.CTkButton(
            self.sidebar,
            text="🎨 Apariencia",
            command=lambda: self._switch_section("appearance"),
            height=40,
            fg_color="transparent",
            hover_color=("#c0c0c0", "#404040"),
            anchor="w",
            font=ctk.CTkFont(size=13)
        )
        self.nav_buttons["appearance"].pack(fill="x", padx=10, pady=5)

        # Highlight current section
        self._highlight_nav_button("grouping")

    def _create_content_area(self):
        """Create right content area."""
        self.content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Create frames for each section
        self.section_frames: Dict[str, ctk.CTkFrame] = {}

        # Grouping section
        self.section_frames["grouping"] = self._create_grouping_section()
        self.section_frames["grouping"].grid(row=0, column=0, sticky="nsew")

        # Appearance section
        self.section_frames["appearance"] = self._create_appearance_section()
        self.section_frames["appearance"].grid(row=0, column=0, sticky="nsew")
        self.section_frames["appearance"].grid_remove()

    def _create_grouping_section(self):
        """Create grouping configuration section."""
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # Header
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        header_label = ctk.CTkLabel(
            header_frame,
            text="Configuración de Agrupación",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Configure cómo se agruparán los registros",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

        # Scrollable content
        scroll_frame = ctk.CTkScrollableFrame(frame)
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        scroll_frame.grid_columnconfigure(0, weight=1)

        # Level 1: Year grouping
        self._add_level_card(
            scroll_frame, 0,
            "Nivel 1: Agrupación por Ejercicio",
            "Agrupa los registros por año fiscal",
            "#e8f4f8", "#1a4d5e",
            "year"
        )

        # Level 2: Concept grouping
        self._add_level_card(
            scroll_frame, 1,
            "Nivel 2: Agrupación por Concepto",
            "Agrupa por código de concepto dentro de cada año",
            "#f0e8f8", "#3d2d4d",
            "concept"
        )

        # Level 3: Custom groups
        self._add_custom_groups_section(scroll_frame, 2)

        return frame

    def _add_level_card(self, parent, row, title, description, bg_light, bg_dark, level):
        """Add a level configuration card."""
        card = ctk.CTkFrame(parent, fg_color=(bg_light, bg_dark), corner_radius=8)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 15))
        card.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

        # Description
        desc_label = ctk.CTkLabel(
            card,
            text=description,
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray80")
        )
        desc_label.grid(row=1, column=0, sticky="w", padx=15, pady=(0, 10))

        # Switch
        if level == "year":
            self.year_switch = ctk.CTkSwitch(
                card,
                text="Activar agrupación por ejercicio",
                font=ctk.CTkFont(size=12)
            )
            if self.grouping_config.group_by_year:
                self.year_switch.select()
            self.year_switch.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 15))
        elif level == "concept":
            self.concept_switch = ctk.CTkSwitch(
                card,
                text="Activar sub-agrupación por concepto",
                font=ctk.CTkFont(size=12)
            )
            if self.grouping_config.group_by_concept:
                self.concept_switch.select()
            self.concept_switch.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 15))

    def _add_custom_groups_section(self, parent, row):
        """Add custom groups CRUD section."""
        card = ctk.CTkFrame(parent, fg_color=("#e8f8f0", "#1d4d3d"), corner_radius=8)
        card.grid(row=row, column=0, sticky="nsew", pady=(0, 15))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(4, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            card,
            text="Nivel 3: Grupos Personalizados de Conceptos",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

        # Description
        desc_label = ctk.CTkLabel(
            card,
            text="Cree grupos personalizados combinando múltiples conceptos",
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray80")
        )
        desc_label.grid(row=1, column=0, sticky="w", padx=15, pady=(0, 10))

        # Switch to activate custom groups in visualization
        self.custom_switch = ctk.CTkSwitch(
            card,
            text="Aplicar grupos personalizados en visualización",
            font=ctk.CTkFont(size=12)
        )
        if self.grouping_config.group_by_custom:
            self.custom_switch.select()
        self.custom_switch.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 15))

        # Add button
        add_btn = ctk.CTkButton(
            card,
            text="+ Nuevo Grupo",
            command=self._add_custom_group,
            width=120,
            height=32
        )
        add_btn.grid(row=3, column=0, sticky="e", padx=15, pady=(0, 10))

        # Table frame
        table_frame = ctk.CTkFrame(card, fg_color="transparent")
        table_frame.grid(row=4, column=0, sticky="nsew", padx=15, pady=(0, 15))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        # Create table
        columns = ("name", "concepts", "count")
        self.groups_table = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=8
        )

        # Define headings
        self.groups_table.heading("name", text="Nombre del Grupo")
        self.groups_table.heading("concepts", text="Conceptos")
        self.groups_table.heading("count", text="Nº")

        # Define column widths
        self.groups_table.column("name", width=200, anchor="w")
        self.groups_table.column("concepts", width=350, anchor="w")
        self.groups_table.column("count", width=50, anchor="center")

        # Scrollbar
        vsb = ttk.Scrollbar(table_frame, orient="vertical",
                           command=self.groups_table.yview)
        self.groups_table.configure(yscrollcommand=vsb.set)

        # Grid
        self.groups_table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        # Table buttons
        table_btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        table_btn_frame.grid(row=4, column=0, sticky="ew", padx=15, pady=(0, 15))

        edit_btn = ctk.CTkButton(
            table_btn_frame,
            text="Editar",
            command=self._edit_selected_group,
            width=100,
            height=32
        )
        edit_btn.pack(side="left", padx=(0, 5))

        delete_btn = ctk.CTkButton(
            table_btn_frame,
            text="Eliminar",
            command=self._delete_selected_group,
            width=100,
            height=32,
            fg_color="red",
            hover_color="darkred"
        )
        delete_btn.pack(side="left")

        # Populate table
        self._refresh_groups_table()

        return card

    def _refresh_groups_table(self):
        """Refresh the groups table."""
        # Clear table
        for item in self.groups_table.get_children():
            self.groups_table.delete(item)

        # Populate with current groups
        for group in self.grouping_config.custom_groups:
            concepts_str = ", ".join(
                [f"{self.grouping_config.get_concept_name(code)} ({code})"
                 for code in group.concept_codes]
            ) if group.concept_codes else "Ninguno"

            self.groups_table.insert(
                "", "end",
                values=(group.name, concepts_str, len(group.concept_codes))
            )

    def _add_custom_group(self):
        """Open dialog to add a new custom group."""
        GroupEditorDialog(self, None, self.grouping_config,
                         self.current_records, self._on_group_saved)

    def _edit_selected_group(self):
        """Edit the selected group."""
        selection = self.groups_table.selection()
        if not selection:
            messagebox.showwarning("Selección requerida",
                                  "Por favor seleccione un grupo para editar.")
            return

        # Get selected group
        item = self.groups_table.item(selection[0])
        group_name = item['values'][0]

        # Find group in config
        group = None
        for g in self.grouping_config.custom_groups:
            if g.name == group_name:
                group = g
                break

        if group:
            GroupEditorDialog(self, group, self.grouping_config,
                            self.current_records, self._on_group_saved)

    def _delete_selected_group(self):
        """Delete the selected group."""
        selection = self.groups_table.selection()
        if not selection:
            messagebox.showwarning("Selección requerida",
                                  "Por favor seleccione un grupo para eliminar.")
            return

        item = self.groups_table.item(selection[0])
        group_name = item['values'][0]

        if messagebox.askyesno("Confirmar Eliminación",
                              f"¿Está seguro de que desea eliminar el grupo '{group_name}'?"):
            self.grouping_config.remove_custom_group(group_name)
            self._refresh_groups_table()

    def _on_group_saved(self, group: ConceptGroup, is_new: bool):
        """Callback when a group is saved."""
        if is_new:
            self.grouping_config.add_custom_group(group.name, group.concept_codes)
        else:
            # Update existing group
            for g in self.grouping_config.custom_groups:
                if g.name == group.name:
                    g.concept_codes = group.concept_codes
                    break

        self._refresh_groups_table()

    def _create_appearance_section(self):
        """Create appearance configuration section."""
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        header_label = ctk.CTkLabel(
            header_frame,
            text="Configuración de Apariencia",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Personalice la apariencia de las tablas",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

        # Scrollable content
        scroll_frame = ctk.CTkScrollableFrame(frame)
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        scroll_frame.grid_columnconfigure(0, weight=1)

        # Font family card
        font_family_card = ctk.CTkFrame(scroll_frame, fg_color=("#e8f4f8", "#1a4d5e"),
                                       corner_radius=8)
        font_family_card.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        font_family_card.grid_columnconfigure(1, weight=1)

        font_family_title = ctk.CTkLabel(
            font_family_card,
            text="Fuente de las Tablas",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        font_family_title.grid(row=0, column=0, columnspan=2, sticky="w",
                              padx=15, pady=(15, 5))

        font_family_desc = ctk.CTkLabel(
            font_family_card,
            text="Seleccione la fuente para mostrar los datos en las tablas",
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray80")
        )
        font_family_desc.grid(row=1, column=0, columnspan=2, sticky="w",
                             padx=15, pady=(0, 15))

        font_family_label = ctk.CTkLabel(
            font_family_card,
            text="Fuente:",
            font=ctk.CTkFont(size=12)
        )
        font_family_label.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 15))

        self.font_family_var = tk.StringVar(value=self.appearance_config.font_family)
        self.font_family_combo = ctk.CTkOptionMenu(
            font_family_card,
            variable=self.font_family_var,
            values=AppearanceConfig.AVAILABLE_FONTS,
            width=200
        )
        self.font_family_combo.grid(row=2, column=1, sticky="w", padx=(10, 15),
                                   pady=(0, 15))

        # Font size card
        font_size_card = ctk.CTkFrame(scroll_frame, fg_color=("#f0e8f8", "#3d2d4d"),
                                     corner_radius=8)
        font_size_card.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        font_size_card.grid_columnconfigure(1, weight=1)

        font_size_title = ctk.CTkLabel(
            font_size_card,
            text="Tamaño de Fuente",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        font_size_title.grid(row=0, column=0, columnspan=2, sticky="w",
                            padx=15, pady=(15, 5))

        font_size_desc = ctk.CTkLabel(
            font_size_card,
            text="Ajuste el tamaño de la fuente en las tablas (8-14 puntos)",
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray80")
        )
        font_size_desc.grid(row=1, column=0, columnspan=2, sticky="w",
                           padx=15, pady=(0, 15))

        font_size_label = ctk.CTkLabel(
            font_size_card,
            text="Tamaño:",
            font=ctk.CTkFont(size=12)
        )
        font_size_label.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 15))

        self.font_size_var = tk.IntVar(value=self.appearance_config.font_size)
        self.font_size_slider = ctk.CTkSlider(
            font_size_card,
            from_=8,
            to=14,
            number_of_steps=6,
            variable=self.font_size_var,
            width=200
        )
        self.font_size_slider.grid(row=2, column=1, sticky="w", padx=(10, 15),
                                  pady=(0, 15))

        # Display current value
        self.font_size_value_label = ctk.CTkLabel(
            font_size_card,
            text=f"{self.font_size_var.get()} pt",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.font_size_value_label.grid(row=2, column=2, sticky="w",
                                       padx=(5, 15), pady=(0, 15))

        # Update label when slider changes
        self.font_size_var.trace_add("write",
                                     lambda *args: self.font_size_value_label.configure(
                                         text=f"{self.font_size_var.get()} pt"))

        return frame

    def _switch_section(self, section: str):
        """Switch to a different configuration section."""
        # Hide all sections
        for name, frame in self.section_frames.items():
            frame.grid_remove()

        # Show selected section
        self.section_frames[section].grid()

        # Update navigation highlight
        self._highlight_nav_button(section)

        self.current_section = section

    def _highlight_nav_button(self, section: str):
        """Highlight the active navigation button."""
        for name, button in self.nav_buttons.items():
            if name == section:
                button.configure(fg_color=("#4a90e2", "#1f5a8a"))
            else:
                button.configure(fg_color="transparent")

    def _create_button_bar(self):
        """Create button bar at bottom."""
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew",
                         padx=20, pady=(0, 20))
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Save button
        save_btn = ctk.CTkButton(
            button_frame,
            text="Guardar",
            command=self._save_config,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40
        )
        save_btn.grid(row=0, column=0, padx=5, sticky="ew")

        # Reset button
        reset_btn = ctk.CTkButton(
            button_frame,
            text="Restaurar Predeterminados",
            command=self._reset_config,
            fg_color="gray40",
            hover_color="gray30",
            height=40
        )
        reset_btn.grid(row=0, column=1, padx=5, sticky="ew")

        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancelar",
            command=self.destroy,
            fg_color="gray50",
            hover_color="gray40",
            height=40
        )
        cancel_btn.grid(row=0, column=2, padx=5, sticky="ew")

    def _save_config(self):
        """Save configuration and close dialog."""
        # Update grouping config from UI
        self.grouping_config.group_by_year = self.year_switch.get()
        self.grouping_config.group_by_concept = self.concept_switch.get()
        self.grouping_config.group_by_custom = self.custom_switch.get()

        # Update appearance config from UI
        self.appearance_config.font_family = self.font_family_var.get()
        self.appearance_config.font_size = self.font_size_var.get()

        # Call save callback
        self.on_save(self.grouping_config, self.appearance_config)

        messagebox.showinfo("Configuración Guardada",
                           "La configuración se ha guardado correctamente.")
        self.destroy()

    def _reset_config(self):
        """Reset configuration to defaults."""
        if messagebox.askyesno(
            "Confirmar Restauración",
            "¿Está seguro de que desea restaurar la configuración predeterminada?\n"
            "Se perderán todos los grupos personalizados."
        ):
            # Reset to defaults
            self.grouping_config.group_by_year = True
            self.grouping_config.group_by_concept = False
            self.grouping_config.custom_groups = []

            self.appearance_config.font_family = "Segoe UI"
            self.appearance_config.font_size = 10

            # Update UI
            self.year_switch.select()
            self.concept_switch.deselect()
            self._refresh_groups_table()

            self.font_family_var.set("Segoe UI")
            self.font_size_var.set(10)


class GroupEditorDialog(ctk.CTkToplevel):
    """Dialog for creating/editing a custom concept group with intuitive selectors."""

    def __init__(self, parent, group: Optional[ConceptGroup],
                 grouping_config: GroupingConfig,
                 current_records: List[TributeRecord],
                 on_save: Callable[[ConceptGroup, bool], None]):
        """
        Initialize group editor dialog.

        Args:
            parent: Parent window
            group: Existing group to edit, or None for new group
            grouping_config: Grouping configuration for concept name lookup
            current_records: Current records to extract available concepts
            on_save: Callback function when group is saved (group, is_new)
        """
        super().__init__(parent)

        self.group = group
        self.is_new = group is None
        self.grouping_config = grouping_config
        self.current_records = current_records
        self.on_save = on_save

        # Extract available concepts from records
        self.available_concepts = self._extract_concepts()

        # Selected concept codes
        self.selected_codes = set(group.concept_codes if group else [])

        # Window setup
        self.title("Nuevo Grupo" if self.is_new else "Editar Grupo")
        self.geometry("700x600")

        # Make it modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

        # Setup UI
        self._setup_ui()

    def _extract_concepts(self) -> Dict[str, str]:
        """Extract available concepts from current records."""
        concepts = {}
        for record in self.current_records:
            code = self.grouping_config.get_concept_code(record.clave_recaudacion)
            if code and code not in concepts:
                concepts[code] = record.concepto
        return concepts

    def _setup_ui(self):
        """Setup the user interface."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Group name
        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        name_frame.grid_columnconfigure(1, weight=1)

        name_label = ctk.CTkLabel(
            name_frame,
            text="Nombre del Grupo:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        name_label.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.name_entry = ctk.CTkEntry(
            name_frame,
            placeholder_text="Ej: Impuestos Directos",
            font=ctk.CTkFont(size=12)
        )
        self.name_entry.grid(row=0, column=1, sticky="ew")

        if not self.is_new:
            self.name_entry.insert(0, self.group.name)

        # Concept selection section
        concepts_label = ctk.CTkLabel(
            self,
            text="Seleccione los Conceptos para este Grupo:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        concepts_label.grid(row=1, column=0, sticky="w", padx=20, pady=(10, 5))

        # Scrollable frame for concept checkboxes
        self.concepts_frame = ctk.CTkScrollableFrame(self, height=350)
        self.concepts_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=5)
        self.concepts_frame.grid_columnconfigure(0, weight=1)

        # Create checkboxes for each concept
        self.concept_vars = {}
        if self.available_concepts:
            row = 0
            for code in sorted(self.available_concepts.keys()):
                name = self.available_concepts[code]

                var = tk.BooleanVar(value=code in self.selected_codes)
                self.concept_vars[code] = var

                cb = ctk.CTkCheckBox(
                    self.concepts_frame,
                    text=f"{name} (Código: {code})",
                    variable=var,
                    font=ctk.CTkFont(size=11)
                )
                cb.grid(row=row, column=0, sticky="w", padx=10, pady=5)
                row += 1
        else:
            # No concepts available
            no_concepts_label = ctk.CTkLabel(
                self.concepts_frame,
                text="No hay conceptos disponibles.\nCargue un archivo primero.",
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray60")
            )
            no_concepts_label.pack(pady=40)

        # Button bar
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 20))
        button_frame.grid_columnconfigure((0, 1), weight=1)

        save_btn = ctk.CTkButton(
            button_frame,
            text="Guardar",
            command=self._save_group,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40
        )
        save_btn.grid(row=0, column=0, padx=5, sticky="ew")

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancelar",
            command=self.destroy,
            fg_color="gray50",
            hover_color="gray40",
            height=40
        )
        cancel_btn.grid(row=0, column=1, padx=5, sticky="ew")

    def _save_group(self):
        """Save the group."""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "El nombre del grupo no puede estar vacío.")
            return

        # Collect selected concept codes
        concept_codes = [code for code, var in self.concept_vars.items() if var.get()]

        if not concept_codes:
            messagebox.showwarning("Advertencia",
                                  "Debe seleccionar al menos un concepto para el grupo.")
            return

        # Create or update group
        group = ConceptGroup(name=name, concept_codes=concept_codes)

        # Call save callback
        self.on_save(group, self.is_new)
        self.destroy()

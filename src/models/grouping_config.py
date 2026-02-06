"""
Configuration models for application settings.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
import json
from pathlib import Path


@dataclass
class AppearanceConfig:
    """
    Configuration for application appearance settings.
    """
    font_family: str = "Segoe UI"  # Default system font
    font_size: int = 10  # Base font size

    # Available font families
    AVAILABLE_FONTS = [
        "Segoe UI",
        "Arial",
        "Helvetica",
        "Courier New",
        "Times New Roman",
        "Verdana"
    ]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'font_family': self.font_family,
            'font_size': self.font_size
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AppearanceConfig':
        """Create from dictionary."""
        return cls(
            font_family=data.get('font_family', 'Segoe UI'),
            font_size=data.get('font_size', 10)
        )

    def save_to_file(self, file_path: Path):
        """Save configuration to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, file_path: Path) -> 'AppearanceConfig':
        """Load configuration from JSON file."""
        if not file_path.exists():
            return cls()

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return cls.from_dict(data)


@dataclass
class ConceptGroup:
    """
    Represents a custom group of concepts.
    """
    name: str
    concept_codes: List[str] = field(default_factory=list)  # List of concept codes (e.g., '208', '100')

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'concept_codes': self.concept_codes
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ConceptGroup':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            concept_codes=data.get('concept_codes', [])
        )


@dataclass
class GroupingConfig:
    """
    Configuration for grouping criteria.

    Levels:
    1. Year grouping (default: enabled)
    2. Concept grouping (extract code from 'clave_recaudacion')
    3. Custom concept groups (with activation switch)
    """
    # Level 1: Group by year
    group_by_year: bool = True

    # Level 2: Group by concept
    group_by_concept: bool = False

    # Level 3: Custom concept groups
    group_by_custom: bool = False  # Control if custom groups are applied in visualization
    custom_groups: List[ConceptGroup] = field(default_factory=list)

    # Concept names for reference (code -> name mapping)
    concept_names: Dict[str, str] = field(default_factory=dict)

    def get_concept_code(self, clave_recaudacion: str) -> str:
        """
        Extract concept code from 'clave_recaudacion'.

        Example: '2024.20.100.208' -> '208'
        """
        if not clave_recaudacion:
            return ""

        parts = clave_recaudacion.split('.')
        #print("clave recaudacion parts:", parts if parts else "no extraida", " code extracted:", parts[-1] if parts else "")
        if parts:
            return parts[-1].strip()
        return ""
    
    def get_concept_code_for_pdfs(self, clave_recaudacion: str) -> str:
        """
        Extract concept code from 'clave_recaudacion'.

        Example: '026/2024/20/100/208' -> '208'
        """
        if not clave_recaudacion:
            return ""

        parts = clave_recaudacion.split('/')
        if parts:
            return parts[-1].strip()
        return ""

    def get_concept_name(self, concept_code: str) -> str:
        """Get concept name for a code, or return the code if name not found."""
        return self.concept_names.get(concept_code, concept_code)

    def add_custom_group(self, name: str, concept_codes: List[str]):
        """Add a new custom concept group."""
        self.custom_groups.append(ConceptGroup(name=name, concept_codes=concept_codes))

    def remove_custom_group(self, group_name: str):
        """Remove a custom group by name."""
        self.custom_groups = [g for g in self.custom_groups if g.name != group_name]

    def get_custom_group_for_concept(self, concept_code: str) -> Optional[str]:
        """Get the custom group name for a concept code, if any."""
        for group in self.custom_groups:
            if concept_code in group.concept_codes:
                return group.name
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'group_by_year': self.group_by_year,
            'group_by_concept': self.group_by_concept,
            'group_by_custom': self.group_by_custom,
            'custom_groups': [g.to_dict() for g in self.custom_groups],
            'concept_names': self.concept_names
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GroupingConfig':
        """Create from dictionary."""
        config = cls(
            group_by_year=data.get('group_by_year', True),
            group_by_concept=data.get('group_by_concept', False),
            group_by_custom=data.get('group_by_custom', False),
            concept_names=data.get('concept_names', {})
        )

        # Load custom groups
        for group_data in data.get('custom_groups', []):
            config.custom_groups.append(ConceptGroup.from_dict(group_data))

        return config

    def save_to_file(self, file_path: Path):
        """Save configuration to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, file_path: Path) -> 'GroupingConfig':
        """Load configuration from JSON file."""
        if not file_path.exists():
            return cls()  # Return default configuration

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return cls.from_dict(data)


@dataclass
class PDFExtractionConfig:
    """
    Configuration for PDF extraction settings.
    Controls how pdfplumber extracts tables from PDF documents.
    """
    # Estrategia horizontal para detección de bordes de tabla
    # Opciones: "lines" (default), "lines_strict"
    horizontal_strategy: str = "lines"

    # Estrategias disponibles
    AVAILABLE_STRATEGIES = ["lines", "lines_strict"]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'horizontal_strategy': self.horizontal_strategy
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PDFExtractionConfig':
        """Create from dictionary."""
        return cls(
            horizontal_strategy=data.get('horizontal_strategy', 'lines')
        )

    def save_to_file(self, file_path: Path):
        """Save configuration to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, file_path: Path) -> 'PDFExtractionConfig':
        """Load configuration from JSON file."""
        if not file_path.exists():
            return cls()

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return cls.from_dict(data)

    def get_table_settings(self) -> Dict[str, Any]:
        """
        Get pdfplumber table settings dictionary.

        Returns:
            Dictionary with settings to pass to page.extract_tables()
        """
        return {
            'horizontal_strategy': self.horizontal_strategy
        }

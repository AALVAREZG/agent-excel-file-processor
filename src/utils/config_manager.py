"""
Configuration manager for persistent application settings.
"""
from pathlib import Path
from typing import Optional
import os

from src.models.grouping_config import GroupingConfig, AppearanceConfig, PDFExtractionConfig


class ConfigManager:
    """Manages application configuration with file persistence."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_dir: Directory to store configuration files.
                       Defaults to user's home directory/.liquidacion-opaef/
        """
        if config_dir is None:
            # Use user's home directory
            home = Path.home()
            self.config_dir = home / '.liquidacion-opaef'
        else:
            self.config_dir = config_dir

        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Configuration file paths
        self.grouping_config_path = self.config_dir / 'grouping_config.json'
        self.appearance_config_path = self.config_dir / 'appearance_config.json'
        self.extraction_config_path = self.config_dir / 'extraction_config.json'

        # Load or create default configuration
        self.grouping_config = self._load_grouping_config()
        self.appearance_config = self._load_appearance_config()
        self.extraction_config = self._load_extraction_config()

    def _load_grouping_config(self) -> GroupingConfig:
        """Load grouping configuration from file or create default."""
        if self.grouping_config_path.exists():
            try:
                return GroupingConfig.load_from_file(self.grouping_config_path)
            except Exception as e:
                print(f"Error loading configuration: {e}")
                return GroupingConfig()  # Return default on error
        else:
            # Create default configuration
            config = GroupingConfig()
            self.save_grouping_config(config)
            return config

    def save_grouping_config(self, config: GroupingConfig):
        """Save grouping configuration to file."""
        try:
            config.save_to_file(self.grouping_config_path)
            self.grouping_config = config
        except Exception as e:
            print(f"Error saving configuration: {e}")
            raise

    def get_grouping_config(self) -> GroupingConfig:
        """Get current grouping configuration."""
        return self.grouping_config

    def update_grouping_config(self, **kwargs):
        """
        Update grouping configuration with new values.

        Args:
            **kwargs: Configuration attributes to update
        """
        for key, value in kwargs.items():
            if hasattr(self.grouping_config, key):
                setattr(self.grouping_config, key, value)

        self.save_grouping_config(self.grouping_config)

    def reset_grouping_config(self):
        """Reset grouping configuration to defaults."""
        self.grouping_config = GroupingConfig()
        self.save_grouping_config(self.grouping_config)

    def _load_appearance_config(self) -> AppearanceConfig:
        """Load appearance configuration from file or create default."""
        if self.appearance_config_path.exists():
            try:
                return AppearanceConfig.load_from_file(self.appearance_config_path)
            except Exception as e:
                print(f"Error loading appearance configuration: {e}")
                return AppearanceConfig()
        else:
            config = AppearanceConfig()
            self.save_appearance_config(config)
            return config

    def save_appearance_config(self, config: AppearanceConfig):
        """Save appearance configuration to file."""
        try:
            config.save_to_file(self.appearance_config_path)
            self.appearance_config = config
        except Exception as e:
            print(f"Error saving appearance configuration: {e}")
            raise

    def get_appearance_config(self) -> AppearanceConfig:
        """Get current appearance configuration."""
        return self.appearance_config

    def reset_appearance_config(self):
        """Reset appearance configuration to defaults."""
        self.appearance_config = AppearanceConfig()
        self.save_appearance_config(self.appearance_config)

    def _load_extraction_config(self) -> PDFExtractionConfig:
        """Load extraction configuration from file or create default."""
        if self.extraction_config_path.exists():
            try:
                return PDFExtractionConfig.load_from_file(self.extraction_config_path)
            except Exception as e:
                print(f"Error loading extraction configuration: {e}")
                return PDFExtractionConfig()
        else:
            config = PDFExtractionConfig()
            self.save_extraction_config(config)
            return config

    def save_extraction_config(self, config: PDFExtractionConfig):
        """Save extraction configuration to file."""
        try:
            config.save_to_file(self.extraction_config_path)
            self.extraction_config = config
        except Exception as e:
            print(f"Error saving extraction configuration: {e}")
            raise

    def get_extraction_config(self) -> PDFExtractionConfig:
        """Get current extraction configuration."""
        return self.extraction_config

    def update_extraction_config(self, **kwargs):
        """
        Update extraction configuration with new values.

        Args:
            **kwargs: Configuration attributes to update
        """
        for key, value in kwargs.items():
            if hasattr(self.extraction_config, key):
                setattr(self.extraction_config, key, value)

        self.save_extraction_config(self.extraction_config)

    def reset_extraction_config(self):
        """Reset extraction configuration to defaults."""
        self.extraction_config = PDFExtractionConfig()
        self.save_extraction_config(self.extraction_config)

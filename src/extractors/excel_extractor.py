"""
Excel Extractor for Recaudation Data (Cuenta Recaudatoria Anual).

This module reads Excel files containing annual recaudation data from agents,
with columns: ENT, C_EJERCICIO, C_CONCEPTO, CLAVE_C, CLAVE_R, C_CARGO,
C_DATAS, C_VOLUNTARIA, C_EJECUTIVA, C_PENDIENTE
"""
import pandas as pd
from decimal import Decimal
from datetime import date
from typing import List, Optional
from pathlib import Path

from src.models.liquidation import (
    LiquidationDocument,
    TributeRecord,
    ExerciseSummary
)


class ExcelExtractionError(Exception):
    """Raised when Excel extraction fails."""
    pass


class RecaudationExcelExtractor:
    """
    Extracts data from annual recaudation Excel files.
    """

    # Expected column names in Excel file
    EXPECTED_COLUMNS = {
        'ENT', 'C_EJERCICIO', 'C_CONCEPTO', 'CLAVE_C', 'CLAVE_R',
        'C_CARGO', 'C_DATAS', 'C_VOLUNTARIA', 'C_EJECUTIVA', 'C_PENDIENTE'
    }

    def __init__(self, excel_path: str):
        """
        Initialize extractor with Excel file path.

        Args:
            excel_path: Path to the Excel file to extract

        Raises:
            FileNotFoundError: If file doesn't exist
            ExcelExtractionError: If file cannot be read
        """
        self.excel_path = Path(excel_path)
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_path}")

    def extract(self) -> LiquidationDocument:
        """
        Extract complete data from Excel file.

        Returns:
            LiquidationDocument with all extracted data

        Raises:
            ExcelExtractionError: If extraction fails
        """
        try:
            # Read Excel file
            df = pd.read_excel(self.excel_path)

            # Validate columns
            self._validate_columns(df)

            # Clean data
            df = self._clean_dataframe(df)

            # Extract entity information from first row
            entity_code = str(df['ENT'].iloc[0]) if len(df) > 0 else "N/A"

            # Extract unique years for document year (use most recent)
            years = sorted(df['C_EJERCICIO'].unique(), reverse=True)
            document_year = int(years[0]) if len(years) > 0 else date.today().year

            # Create tribute records
            tribute_records = self._extract_tribute_records(df)

            # Create exercise summaries (grouped by year)
            exercise_summaries = self._create_exercise_summaries(tribute_records)

            # Calculate global totals
            totals = self._calculate_totals(tribute_records)

            # Create document with minimal header
            document = LiquidationDocument(
                # Header fields (adapted for annual file)
                ejercicio=document_year,
                entidad=f"Entidad {entity_code}",

                # Main data
                tribute_records=tribute_records,
                exercise_summaries=exercise_summaries,

                # Totals
                total_c_cargo=totals['c_cargo'],
                total_c_datas=totals['c_datas'],
                total_c_voluntaria=totals['c_voluntaria'],
                total_c_ejecutiva=totals['c_ejecutiva'],
                total_cc_pendiente=totals['cc_pendiente']
            )

            return document

        except Exception as e:
            raise ExcelExtractionError(f"Failed to extract Excel data: {str(e)}") from e

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """
        Validate that required columns are present.

        Args:
            df: DataFrame to validate

        Raises:
            ExcelExtractionError: If required columns are missing
        """
        actual_columns = set(df.columns)
        missing_columns = self.EXPECTED_COLUMNS - actual_columns

        if missing_columns:
            raise ExcelExtractionError(
                f"Missing required columns: {', '.join(missing_columns)}"
            )

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and prepare DataFrame for processing.

        Args:
            df: Raw DataFrame

        Returns:
            Cleaned DataFrame
        """
        # Make a copy to avoid modifying original
        df = df.copy()

        # Remove rows where all numeric columns are NaN or 0
        numeric_cols = ['C_CARGO', 'C_VOLUNTARIA', 'C_EJECUTIVA', 'C_PENDIENTE']
        df = df.dropna(subset=numeric_cols, how='all')

        # Fill NaN values in numeric columns with 0
        for col in numeric_cols:
            df[col] = df[col].fillna(0)

        # Fill NaN values in string columns
        string_cols = ['C_CONCEPTO', 'CLAVE_C', 'CLAVE_R']
        for col in string_cols:
            df[col] = df[col].fillna('')

        # Convert year to int
        df['C_EJERCICIO'] = df['C_EJERCICIO'].astype(int)

        return df

    def _extract_tribute_records(self, df: pd.DataFrame) -> List[TributeRecord]:
        """
        Extract tribute records from DataFrame.

        Args:
            df: Cleaned DataFrame

        Returns:
            List of TributeRecord objects
        """
        records = []

        for _, row in df.iterrows():
            # Direct mapping from Excel columns - no format conversion needed
            # Excel already has correct decimal values (e.g., 553.61)
            record = TributeRecord(
                ejercicio=int(row['C_EJERCICIO']),
                concepto=str(row['C_CONCEPTO']).strip(),
                clave_contabilidad=str(row['CLAVE_C']).strip(),
                clave_recaudacion=str(row['CLAVE_R']).strip(),
                c_cargo=Decimal(str(row['C_CARGO'])),
                c_datas=Decimal(str(row['C_DATAS'])),
                c_voluntaria=Decimal(str(row['C_VOLUNTARIA'])),
                c_ejecutiva=Decimal(str(row['C_EJECUTIVA'])),
                cc_pendiente=Decimal(str(row['C_PENDIENTE']))
            )
            records.append(record)

        return records

    def _create_exercise_summaries(self, records: List[TributeRecord]) -> List[ExerciseSummary]:
        """
        Create summaries grouped by fiscal year.

        Args:
            records: List of tribute records

        Returns:
            List of ExerciseSummary objects, one per year
        """
        # Group records by year
        by_year = {}
        for record in records:
            if record.ejercicio not in by_year:
                by_year[record.ejercicio] = []
            by_year[record.ejercicio].append(record)

        # Create summaries
        summaries = []
        for year, year_records in sorted(by_year.items()):
            summary = ExerciseSummary(
                ejercicio=year,
                c_cargo=sum(r.c_cargo for r in year_records),
                c_datas=sum(r.c_datas for r in year_records),
                c_voluntaria=sum(r.c_voluntaria for r in year_records),
                c_ejecutiva=sum(r.c_ejecutiva for r in year_records),
                cc_pendiente=sum(r.cc_pendiente for r in year_records),
                records=year_records
            )
            summaries.append(summary)

        return summaries

    def _calculate_totals(self, records: List[TributeRecord]) -> dict:
        """
        Calculate global totals from all records.

        Args:
            records: List of tribute records

        Returns:
            Dictionary with total amounts
        """
        return {
            'c_cargo': sum(r.c_cargo for r in records),
            'c_datas': sum(r.c_datas for r in records),
            'c_voluntaria': sum(r.c_voluntaria for r in records),
            'c_ejecutiva': sum(r.c_ejecutiva for r in records),
            'cc_pendiente': sum(r.cc_pendiente for r in records)
        }



def extract_recaudation_excel(excel_path: str) -> LiquidationDocument:
    """
    Convenience function to extract a recaudation Excel file.

    Args:
        excel_path: Path to Excel file

    Returns:
        Extracted LiquidationDocument

    Raises:
        ExcelExtractionError: If extraction fails
    """
    extractor = RecaudationExcelExtractor(excel_path)
    return extractor.extract()

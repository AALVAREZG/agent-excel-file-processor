"""
PDF Extractor for Liquidation Documents (Documentos de Liquidación).

This module uses pdfplumber to extract structured data from PDF liquidation documents.
Accuracy is critical for accounting purposes.
"""
import re
import pdfplumber
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from src.models.liquidation import (
    LiquidationDocument,
    TributeRecord,
    ExerciseSummary,
   
)


class PDFExtractionError(Exception):
    """Raised when PDF extraction fails."""
    pass


class LiquidationPDFExtractor:
    """
    Extracts data from liquidation PDF documents with high accuracy.
    """

    def __init__(self, pdf_path: str, table_settings: Optional[Dict[str, Any]] = None):
        """
        Initialize extractor with PDF file path.

        Args:
            pdf_path: Path to the PDF file to extract
            table_settings: Optional dictionary of pdfplumber table extraction settings
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Store table extraction settings
        self.table_settings = table_settings if table_settings is not None else {}

        # Store partial row from previous page (for cross-page continuations)
        self._pending_partial_row = None
        # Store last valid data row from previous page (for backward merging across pages)
        self._last_processed_row = None
        # Flag to signal that the last global record should be replaced (cross-page backward merge)
        self._replace_last_record = False

    def extract(self) -> LiquidationDocument:
        """
        Extract complete liquidation document from PDF.

        Returns:
            LiquidationDocument with all extracted data

        Raises:
            PDFExtractionError: If extraction fails
        """
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                num_pages = len(pdf.pages)

                # Reset pending partial row, last processed row, and replacement flag at start of extraction
                self._pending_partial_row = None
                self._last_processed_row = None
                self._replace_last_record = False

                # Extract header information from page 1
                header_data = self._extract_header(pdf.pages[0])

                # Extract tribute records from ALL pages (multi-page documents)
                tribute_records = []
                exercise_summaries = []

                # Process ALL pages except the VERY LAST ONE (which has totals/summaries)
                # Even the second-to-last page might have tribute records!
                pages_to_process = num_pages - 1 if num_pages > 1 else num_pages
                for page_idx in range(pages_to_process):
                    try:
                        records, summaries = self._extract_tribute_records(pdf.pages[page_idx])

                        # Check if we need to replace the last record (cross-page backward merge)
                        if self._replace_last_record and tribute_records:
                            print(f"DEBUG: Replacing last global record due to cross-page backward merge")
                            tribute_records.pop()
                            self._replace_last_record = False

                        if records:  # Only add if we found actual records
                            tribute_records.extend(records)
                        if summaries:
                            exercise_summaries.extend(summaries)
                    except Exception as e:
                        print(f"Warning: Failed to extract from page {page_idx + 1}: {e}")
                        continue

                # Extract totals and deductions by finding TOTAL table (structure-based, not page-based)
                totals = {'voluntaria': Decimal('0'), 'ejecutiva': Decimal('0'), 'recargo': Decimal('0'),
                         'diputacion_voluntaria': Decimal('0'), 'diputacion_ejecutiva': Decimal('0'),
                         'diputacion_recargo': Decimal('0'), 'liquido': Decimal('0'), 'a_liquidar': Decimal('0')}
                deductions = None
                advance_breakdown = []

                if num_pages >= 2:
                    # Search ALL pages for the TOTAL table (not hardcoded page numbers)
                    totals, deductions, advance_breakdown = self._find_and_extract_totals(pdf.pages)

                # Extract refunds from last page if exists
                refund_records = []
                refund_summaries = []
                if num_pages >= 3:
                    try:
                        refund_records, refund_summaries = self._extract_refunds(pdf.pages[num_pages - 1])
                    except:
                        # If last page fails, try page 2 (original logic)
                        if num_pages >= 3:
                            refund_records, refund_summaries = self._extract_refunds(pdf.pages[2])

                # Build complete document
                doc = LiquidationDocument(
                    ejercicio=header_data['ejercicio'],
                    mandamiento_pago=header_data['mandamiento_pago'],
                    fecha_mandamiento=header_data['fecha_mandamiento'],
                    numero_liquidacion=header_data['numero_liquidacion'],
                    entidad=header_data['entidad'],
                    codigo_entidad=header_data['codigo_entidad'],
                    tribute_records=tribute_records,
                    exercise_summaries=exercise_summaries,
                    total_voluntaria=totals['voluntaria'],
                    total_ejecutiva=totals['ejecutiva'],
                    total_recargo=totals['recargo'],
                    total_diputacion_voluntaria=totals['diputacion_voluntaria'],
                    total_diputacion_ejecutiva=totals['diputacion_ejecutiva'],
                    total_diputacion_recargo=totals['diputacion_recargo'],
                    total_liquido=totals['liquido'],
                    deductions=deductions,
                    advance_breakdown=advance_breakdown,
                    refund_records=refund_records,
                    refund_summaries=refund_summaries,
                    a_liquidar=totals.get('a_liquidar', Decimal('0')),
                    codigo_verificacion=header_data.get('codigo_verificacion'),
                    firmado_por=header_data.get('firmado_por'),
                    fecha_firma=header_data.get('fecha_firma')
                )

                return doc

        except Exception as e:
            raise PDFExtractionError(f"Failed to extract PDF {self.pdf_path}: {str(e)}") from e

    def _extract_header(self, page) -> Dict[str, Any]:
        """Extract header information from page 1."""
        text = page.extract_text()
        header = {}

        # Extract ejercicio (year)
        match = re.search(r'EJERCICIO\s+(\d{4})', text)
        if match:
            header['ejercicio'] = int(match.group(1))

        # Extract mandamiento de pago
        match = re.search(r'Mandamiento de pago:\s*([\d/]+)', text)
        if match:
            header['mandamiento_pago'] = match.group(1)

        # Extract fecha mandamiento
        match = re.search(r'Fecha de mandamiento:\s*(\d{2}/\d{2}/\d{4})', text)
        if match:
            header['fecha_mandamiento'] = datetime.strptime(match.group(1), '%d/%m/%Y').date()

        # Extract numero liquidacion
        match = re.search(r'Número de liquidación:\s*(\d+)', text)
        if match:
            header['numero_liquidacion'] = match.group(1)

        # Extract entidad
        match = re.search(r'\((\d+)\)\s+(.+?)(?=\n|$)', text)
        if match:
            header['codigo_entidad'] = match.group(1)
            header['entidad'] = match.group(2).strip()

        # Extract verification code
        match = re.search(r'Código Seguro De Verificación:\s*(\S+)', text)
        if match:
            header['codigo_verificacion'] = match.group(1)

        # Extract signature info
        match = re.search(r'Firmado Por\s+(.+?)(?=\s+Firmado)', text)
        if match:
            header['firmado_por'] = match.group(1).strip()

        match = re.search(r'Firmado\s+(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})', text)
        if match:
            header['fecha_firma'] = datetime.strptime(match.group(1), '%d/%m/%Y %H:%M:%S')

        return header

    def _is_partial_row(self, row: List[str]) -> bool:
        """
        Detect if a row is partial (concept only, no data).
        This happens when a row is split across pages.

        Returns True if row has a concept but all other cells are empty.
        """
        if not row or len(row) < 8:
            return False

        # Check if first cell has content but rest are empty
        first_cell = str(row[0]).strip() if row[0] else ""
        if not first_cell:
            return False

        # Skip if it's a header or total row
        if any(keyword in first_cell.upper() for keyword in ['CONCEPTO', 'CLAVE', 'TOTAL EJERCICIO']):
            return False

        # Check if all remaining cells (at least the numeric columns) are empty
        # Columns 3-9 should have numeric data for valid records
        numeric_cells = row[3:10] if len(row) > 9 else row[3:]
        all_empty = all(not str(cell).strip() or str(cell).strip() == '' for cell in numeric_cells)

        # Also check clave_contabilidad and clave_recaudacion (columns 1-2)
        clave_cells = row[1:3] if len(row) > 2 else []
        claves_empty = all(not str(cell).strip() or str(cell).strip() == '' for cell in clave_cells)

        return all_empty and claves_empty

    def _merge_partial_row(self, partial_row: List[str], continuation_row: List[str]) -> List[str]:
        """
        Merge a partial row from previous page with its continuation.

        Args:
            partial_row: Row with concept but no data
            continuation_row: Row with data (and possibly additional concept text)

        Returns:
            Merged complete row
        """
        merged = []

        # Merge concept (column 0)
        partial_concept = str(partial_row[0]).strip() if partial_row[0] else ""
        continuation_concept = str(continuation_row[0]).strip() if continuation_row[0] else ""

        # Combine concepts with a space
        if partial_concept and continuation_concept:
            merged.append(f"{partial_concept} {continuation_concept}")
        elif partial_concept:
            merged.append(partial_concept)
        else:
            merged.append(continuation_concept)

        # For remaining columns, prefer continuation_row data
        max_len = max(len(partial_row), len(continuation_row))
        for i in range(1, max_len):
            partial_val = str(partial_row[i]).strip() if i < len(partial_row) and partial_row[i] else ""
            continuation_val = str(continuation_row[i]).strip() if i < len(continuation_row) and continuation_row[i] else ""

            # Prefer non-empty value, prioritizing continuation
            if continuation_val:
                merged.append(continuation_val)
            elif partial_val:
                merged.append(partial_val)
            else:
                merged.append("")

        return merged

    def _extract_tribute_records(self, page) -> Tuple[List[TributeRecord], List[ExerciseSummary]]:
        """
        Extract tribute records table from page 1.
        This is the most critical extraction - must be highly accurate.
        """
        # Extract table using pdfplumber's table detection with custom settings
        tables = page.extract_tables(table_settings=self.table_settings)

        if not tables:
            raise PDFExtractionError("No tables found on this page")

        tribute_records = []
        exercise_summaries = []
        current_exercise = None
        # Note: self._last_processed_row persists across pages for backward merging

        # Process ALL tables on the page (there may be multiple tables)
        for table_idx, table in enumerate(tables):
            if not table or len(table) < 1:
                continue  # Skip empty tables

            for row in table:

                if not row or len(row) < 8:
                    continue
                print(f"DEBUG: [TABLE_{table_idx}]-[ROW] {row}")

                # Check if we have a pending partial row from previous page
                if self._pending_partial_row is not None:
                    # Skip headers on new page
                    if any(header in str(row[0]).upper() for header in ['CONCEPTO', 'CLAVE']):
                        continue

                    # Check if current row is a continuation (has data)
                    numeric_cells = row[3:10] if len(row) >= 10 else row[3:]
                    has_data = any(str(cell).strip() and str(cell).strip() != ''
                                   for cell in numeric_cells)

                    if has_data:
                        # Merge the pending partial row with this continuation row
                        print(f"DEBUG: Forward merging partial row {self._pending_partial_row[0]} with continuation {row[0]}")
                        merged_row = self._merge_partial_row(self._pending_partial_row, row)
                        print(f"DEBUG: Forward merged result: {merged_row}")

                        # Clear the pending partial
                        self._pending_partial_row = None

                        # Process the merged row and track it
                        row = merged_row
                        # Note: last_processed_row will be updated at the end when record is added
                    else:
                        # This row is also partial or a header, skip it
                        continue

                # Skip header rows
                if any(header in str(row[0]).upper() for header in ['CONCEPTO', 'CLAVE']):
                    continue

                # Check if this is a partial row (can be merged backward or forward)
                if self._is_partial_row(row):
                    print(f"DEBUG: Found partial row: {row[0]}")

                    # ALWAYS try backward merging first (merge with last valid data row)
                    # Partial rows are typically continuations of the previous record's concept
                    # This works ACROSS PAGES because self._last_processed_row persists
                    if self._last_processed_row is not None:
                        print(f"DEBUG: Backward merging with last valid row: {self._last_processed_row[0]}")
                        # Merge backward: self._last_processed_row (main concept + data) + row (additional concept text)
                        merged_row = self._merge_partial_row(self._last_processed_row, row)
                        print(f"DEBUG: Backward merged result: {merged_row}")

                        # Check if this is a cross-page merge (local list is empty)
                        if not tribute_records:
                            # Cross-page merge: signal to remove last record from global list
                            print(f"DEBUG: Cross-page backward merge detected - will replace last global record")
                            self._replace_last_record = True
                        else:
                            # Same-page merge: remove from local list
                            tribute_records.pop()

                        # Process the merged row as a new record
                        try:
                            record = self._parse_tribute_row(merged_row, current_exercise)
                            if record:
                                tribute_records.append(record)
                                self._last_processed_row = merged_row
                                print(f"DEBUG: Added backward-merged record")
                        except Exception as e:
                            print(f"Warning: Failed to parse backward-merged row: {e}")
                            # Re-add the original record if merge failed (only for same-page merges)
                            if tribute_records or not self._replace_last_record:
                                if self._last_processed_row:
                                    try:
                                        record = self._parse_tribute_row(self._last_processed_row, current_exercise)
                                        if record:
                                            tribute_records.append(record)
                                    except:
                                        pass
                            # Clear the flag if merge failed
                            self._replace_last_record = False
                    else:
                        # No previous row to merge with - only at document start
                        print(f"DEBUG: No previous valid row found, saving for forward merge (cross-page)")
                        self._pending_partial_row = row

                    continue  # Skip further processing of this partial row

                # Check if this row has MULTIPLE RECORDS merged together (not involving TOTAL EJERCICIO)
                # Example: Two multas records in one row with newlines separating values
                # Detection: clave_contabilidad (row[1]) has multiple values separated by newlines
                clave_cont_cell = str(row[1]) if len(row) > 1 and row[1] else ""
                has_multiple_records = False
                if '\n' in clave_cont_cell:
                    # Count number of clave_contabilidad patterns
                    clave_patterns = re.findall(r'\d{4}/[A-Z]/\d+', clave_cont_cell)
                    if len(clave_patterns) > 1:
                        has_multiple_records = True

                if has_multiple_records:
                    # Split this row into multiple separate rows
                    print(f"DEBUG: Found row with {len(clave_patterns)} merged records")

                    # Determine how many records are merged (by counting newlines in clave_contabilidad)
                    num_records = len(clave_cont_cell.split('\n'))

                    # Split each cell by newlines
                    split_cells = []
                    for cell_idx, cell in enumerate(row):
                        cell_str = str(cell) if cell else ""
                        if '\n' in cell_str:
                            # Special handling for concepto column (index 0)
                            if cell_idx == 0:
                                # For concepto, try to intelligently split by finding repeated patterns
                                # or use the joined text for all records as fallback
                                lines = cell_str.split('\n')
                                # If we have lines that look like they repeat, try to group them
                                # For now, use the complete joined text for all records
                                full_concepto = ' '.join(lines).strip()
                                split_cells.append([full_concepto] * num_records)
                            else:
                                split_cells.append(cell_str.split('\n'))
                        else:
                            # If no newlines, repeat the same value for all records
                            split_cells.append([cell_str] * num_records)

                    # Create separate rows
                    for record_idx in range(num_records):
                        separate_row = []
                        for cell_values in split_cells:
                            # Get the value for this record index
                            if record_idx < len(cell_values):
                                separate_row.append(cell_values[record_idx])
                            else:
                                separate_row.append('')

                        # Process this separate row as a normal tribute record
                        try:
                            record = self._parse_tribute_row(separate_row, current_exercise)
                            if record:
                                tribute_records.append(record)
                                self._last_processed_row = separate_row  # Track last processed row
                                print(f"  - Created record {record_idx + 1}: {record.clave_contabilidad}")
                        except Exception as e:
                            print(f"Warning: Failed to parse split record {record_idx + 1}: {e}")

                    continue  # Skip further processing for this row

                # Check if this row has BOTH record data AND "TOTAL EJERCICIO" merged (PDF formatting issue)
                # Example: "MULTAS 2025/M/0000731\nTRAFICO/CIR\nCULACION\nTOTAL EJERCICIO"
                concepto_text = str(row[0]) if row[0] else ""
                is_merged_row = (
                    '\n' in concepto_text and
                    'TOTAL' in concepto_text.upper() and
                    'EJERCICIO' in concepto_text.upper() and
                    len(concepto_text.split('\n')) > 2  # Has multiple lines before TOTAL
                )

                if is_merged_row:
                    # Split the merged row into record row and total row
                    # First, extract the record from the first lines (before TOTAL EJERCICIO)
                    record_row = []
                    total_row = []

                    # Special handling for concepto column which has the clave_contabilidad embedded
                    # Example: "MULTAS 2025/M/0000731\nTRAFICO/CIR\nCULACION\nTOTAL EJERCICIO"
                    concepto_lines = concepto_text.split('\n')

                    # Extract clave_contabilidad from first line of concepto if row[1] is None
                    clave_contabilidad_extracted = None
                    if row[1] is None or not row[1]:
                        # Look for pattern like "2025/M/0000731" in first line
                        first_line = concepto_lines[0] if concepto_lines else ""
                        match = re.search(r'(\d{4}/[A-Z]/\d+)', first_line)
                        if match:
                            clave_contabilidad_extracted = match.group(1)
                            # Remove it from concepto
                            concepto_lines[0] = first_line.replace(clave_contabilidad_extracted, '').strip()

                    # Build record concepto (all lines except TOTAL EJERCICIO)
                    record_concepto_lines = [line for line in concepto_lines if 'TOTAL EJERCICIO' not in line.upper()]
                    record_row.append('\n'.join(record_concepto_lines))

                    # Build total concepto (just TOTAL EJERCICIO line)
                    total_concepto_lines = [line for line in concepto_lines if 'TOTAL EJERCICIO' in line.upper()]
                    total_row.append(total_concepto_lines[0] if total_concepto_lines else '')

                    # Process remaining columns
                    for idx, cell in enumerate(row[1:], 1):
                        # For clave_contabilidad column, use extracted value if we found one
                        if idx == 1 and clave_contabilidad_extracted:
                            record_row.append(clave_contabilidad_extracted)
                            total_row.append('')
                        elif cell and '\n' in str(cell):
                            lines = str(cell).split('\n')
                            # For other columns, first value is record, second is total
                            record_row.append(lines[0] if len(lines) > 0 else '')
                            total_row.append(lines[1] if len(lines) > 1 else '')
                        else:
                            record_row.append(str(cell) if cell else '')
                            total_row.append('')

                    # Process the record first
                    try:
                        record = self._parse_tribute_row(record_row, current_exercise)
                        if record:
                            tribute_records.append(record)
                            self._last_processed_row = record_row  # Track last processed row
                    except Exception as e:
                        print(f"Warning: Failed to parse merged record row {record_row}: {e}")

                    # Then process the total
                    if any(total_row):
                        match = re.search(r'(\d{4})', total_row[2] if len(total_row) > 2 else total_row[0])
                        if match:
                            year = int(match.group(1))
                            try:
                                summary = self._parse_summary_row(total_row, year)
                                exercise_summaries.append(summary)
                                current_exercise = year
                            except Exception as e:
                                print(f"Warning: Failed to parse merged total row for year {year}: {e}")
                    continue

                # Check if this is a regular TOTAL row (exercise summary)
                if 'TOTAL' in str(row[0]).upper() and 'EJERCICIO' in str(row[0]).upper():
                    # Extract year - try row[2] first (where year usually is), then row[1], then row[0]
                    year_candidates = []
                    if len(row) > 2 and row[2]:
                        year_candidates.append(str(row[2]))
                    if len(row) > 1 and row[1]:
                        year_candidates.append(str(row[1]))
                    year_candidates.append(str(row[0]))

                    match = None
                    for candidate in year_candidates:
                        match = re.search(r'(\d{4})', candidate)
                        if match:
                            break

                    if match:
                        year = int(match.group(1))
                        try:
                            summary = self._parse_summary_row(row, year)
                            exercise_summaries.append(summary)
                            current_exercise = year
                        except Exception as e:
                            print(f"Warning: Failed to parse summary row for year {year}: {e}")
                    continue

                # Parse regular tribute record
                try:
                    record = self._parse_tribute_row(row, current_exercise)
                    if record:
                        tribute_records.append(record)
                        self._last_processed_row = row  # Track for potential backward merging
                except Exception as e:
                    print(f"Warning: Failed to parse row {row}: {e}")
                    continue

        return tribute_records, exercise_summaries

    def _parse_tribute_row(self, row: List[str], ejercicio: Optional[int]) -> Optional[TributeRecord]:
        """
        Parse a single tribute record row.

        Expected columns:
        [CONCEPTO, CLAVE_CONTABILIDAD, CLAVE_RECAUDACION, VOLUNTARIA, EJECUTIVA,
         RECARGO, DIP_VOLUNTARIA, DIP_EJECUTIVA, DIP_RECARGO, LIQUIDO]
        """
        if len(row) < 10:
            return None

        # Clean and parse values - remove newlines and extra spaces
        concepto = str(row[0]).strip() if row[0] else ""
        # Replace newlines and multiple spaces with single space
        concepto = re.sub(r'\s+', ' ', concepto)
        if not concepto or concepto.upper() in ['CONCEPTO', 'TOTAL']:
            return None

        clave_contabilidad = str(row[1]).strip() if row[1] else ""
        clave_recaudacion = str(row[2]).strip() if row[2] else ""

        # Parse amounts - handle thousands separators and decimals
        voluntaria = self._parse_amount(row[3])
        ejecutiva = self._parse_amount(row[4])
        recargo = self._parse_amount(row[5])
        dip_voluntaria = self._parse_amount(row[6])
        dip_ejecutiva = self._parse_amount(row[7])
        dip_recargo = self._parse_amount(row[8])
        liquido = self._parse_amount(row[9])

        # Extract ejercicio (fiscal year) from clave_recaudacion
        # Format: 026/YYYY/xx/xxx/xxx where YYYY is the fiscal year
        # ALWAYS extract from clave_recaudacion first (most reliable source)
        extracted_ejercicio = None
        if clave_recaudacion:
            # Try to match the format 026/YYYY/...
            match = re.search(r'026/(\d{4})/', clave_recaudacion)
            if match:
                extracted_ejercicio = int(match.group(1))
            else:
                # Fallback: try any 4-digit year in clave_recaudacion
                match = re.search(r'(\d{4})', clave_recaudacion)
                if match:
                    year = int(match.group(1))
                    # Validate it's a reasonable year (2000-2030)
                    if 2000 <= year <= 2030:
                        extracted_ejercicio = year

        # If not found in clave_recaudacion, try clave_contabilidad
        if not extracted_ejercicio and clave_contabilidad:
            match = re.search(r'(\d{4})', clave_contabilidad)
            if match:
                year = int(match.group(1))
                if 2000 <= year <= 2030:
                    extracted_ejercicio = year

        # Use extracted year, fall back to parameter, then to default
        if extracted_ejercicio:
            ejercicio = extracted_ejercicio
        elif not ejercicio:
            ejercicio = 2025  # Default fallback

        return TributeRecord(
            concepto=concepto,
            clave_contabilidad=clave_contabilidad,
            clave_recaudacion=clave_recaudacion,
            voluntaria=voluntaria,
            ejecutiva=ejecutiva,
            recargo=recargo,
            diputacion_voluntaria=dip_voluntaria,
            diputacion_ejecutiva=dip_ejecutiva,
            diputacion_recargo=dip_recargo,
            liquido=liquido,
            ejercicio=ejercicio
        )

    def _parse_summary_row(self, row: List[str], ejercicio: int) -> ExerciseSummary:
        """Parse a TOTAL EJERCICIO summary row."""
        # Similar structure to tribute row but for totals
        voluntaria = self._parse_amount(row[3]) if len(row) > 3 else Decimal('0')
        ejecutiva = self._parse_amount(row[4]) if len(row) > 4 else Decimal('0')
        recargo = self._parse_amount(row[5]) if len(row) > 5 else Decimal('0')
        dip_voluntaria = self._parse_amount(row[6]) if len(row) > 6 else Decimal('0')
        dip_ejecutiva = self._parse_amount(row[7]) if len(row) > 7 else Decimal('0')
        dip_recargo = self._parse_amount(row[8]) if len(row) > 8 else Decimal('0')
        liquido = self._parse_amount(row[9]) if len(row) > 9 else Decimal('0')

        return ExerciseSummary(
            ejercicio=ejercicio,
            voluntaria=voluntaria,
            ejecutiva=ejecutiva,
            recargo=recargo,
            diputacion_voluntaria=dip_voluntaria,
            diputacion_ejecutiva=dip_ejecutiva,
            diputacion_recargo=dip_recargo,
            liquido=liquido
        )

    def _find_and_extract_totals(self, pages) -> Tuple[Dict[str, Decimal], DeductionDetail, List[AdvanceBreakdown]]:
        """
        Find and extract totals by searching for TOTAL table structure across ALL pages.
        This is more robust than hardcoded page numbers.

        Returns:
            Tuple of (totals dict, deductions, advance_breakdown)
        """
        totals = {
            'voluntaria': Decimal('0'),
            'ejecutiva': Decimal('0'),
            'recargo': Decimal('0'),
            'diputacion_voluntaria': Decimal('0'),
            'diputacion_ejecutiva': Decimal('0'),
            'diputacion_recargo': Decimal('0'),
            'liquido': Decimal('0'),
            'a_liquidar': Decimal('0')
        }
        deductions = None
        advance_breakdown = []

        # Search all pages for the TOTAL table
        for page_idx, page in enumerate(pages):
            tables = page.extract_tables(table_settings=self.table_settings)

            # Look for TOTAL table by structure
            for table in tables:
                if not table or len(table) < 2:
                    continue

                # Check if this is the TOTAL table
                # Row 0 should have "TOTAL" text
                first_row = table[0]
                if not any('TOTAL' in str(cell).upper() for cell in first_row if cell):
                    continue

                # Row 1 should have multi-line cell with VOLUNTARIA, EJECUTIVA, etc.
                if len(table) < 2:
                    continue

                second_row = table[1]
                multiline_cell = None
                for cell in second_row:
                    if cell and '\n' in str(cell):
                        cell_str = str(cell).upper()
                        if 'VOLUNTARIA' in cell_str and 'EJECUTIVA' in cell_str:
                            multiline_cell = str(cell)
                            break

                if not multiline_cell:
                    continue

                # Found the TOTAL table! Extract values from multi-line cell
                print(f"DEBUG: Found TOTAL table on page {page_idx + 1}")
                lines = multiline_cell.split('\n')

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Match VOLUNTARIA (not DIPUTACIÓN VOLUNTARIA)
                    if line.startswith('VOLUNTARIA'):
                        match = re.search(r'VOLUNTARIA\s+([\d.,]+)', line)
                        if match:
                            totals['voluntaria'] = self._parse_amount(match.group(1))

                    # Match EJECUTIVA (not DIPUTACIÓN EJECUTIVA)
                    elif line.startswith('EJECUTIVA'):
                        match = re.search(r'EJECUTIVA\s+([\d.,]+)', line)
                        if match:
                            totals['ejecutiva'] = self._parse_amount(match.group(1))

                    # Match RECARGO (not DIPUTACIÓN RECARGO)
                    elif line.startswith('RECARGO'):
                        match = re.search(r'RECARGO\s+([\d.,]+)', line)
                        if match:
                            totals['recargo'] = self._parse_amount(match.group(1))

                    # Match DIPUTACIÓN VOLUNTARIA
                    elif 'DIPUTACI' in line.upper() and 'VOLUNTARIA' in line:
                        match = re.search(r'VOLUNTARIA\s+([\d.,]+)', line)
                        if match:
                            totals['diputacion_voluntaria'] = self._parse_amount(match.group(1))

                    # Match DIPUTACIÓN EJECUTIVA
                    elif 'DIPUTACI' in line.upper() and 'EJECUTIVA' in line:
                        match = re.search(r'EJECUTIVA\s+([\d.,]+)', line)
                        if match:
                            totals['diputacion_ejecutiva'] = self._parse_amount(match.group(1))

                    # Match DIPUTACIÓN RECARGO
                    elif 'DIPUTACI' in line.upper() and 'RECARGO' in line:
                        match = re.search(r'RECARGO\s+([\d.,]+)', line)
                        if match:
                            totals['diputacion_recargo'] = self._parse_amount(match.group(1))

                # Check row 2 or next rows for LÍQUIDO
                for row in table[2:]:
                    for cell in row:
                        if cell and re.search(r'L[IÍ]QUIDO', str(cell), re.IGNORECASE):
                            match = re.search(r'L[IÍ]QUIDO\s+([\d.,]+)', str(cell), re.IGNORECASE)
                            if match:
                                totals['liquido'] = self._parse_amount(match.group(1))
                                break

                # Extract A LIQUIDAR from the same page
                page_text = page.extract_text()
                match = re.search(r'A\s+LIQUIDAR\s+([\d.,]+)', page_text)
                if match:
                    totals['a_liquidar'] = self._parse_amount(match.group(1))

                # Extract deductions and advance breakdown from the same page
                try:
                    _, deductions, advance_breakdown = self._extract_page2_data(page)
                except Exception as e:
                    print(f"Warning: Failed to extract deductions from page {page_idx + 1}: {e}")

                # Successfully found and extracted totals, return immediately
                return totals, deductions, advance_breakdown

        # If we didn't find TOTAL table, return defaults
        print("Warning: TOTAL table not found in any page")
        return totals, deductions, advance_breakdown

    def _extract_page2_data(self, page) -> Tuple[Dict[str, Decimal], DeductionDetail, List[AdvanceBreakdown]]:
        """Extract totals, deductions, and advance breakdown from page 2."""
        text = page.extract_text()
        tables = page.extract_tables(table_settings=self.table_settings)

        # Extract TOTAL section from tables first (more reliable)
        totals = {
            'voluntaria': Decimal('0'),
            'ejecutiva': Decimal('0'),
            'recargo': Decimal('0'),
            'diputacion_voluntaria': Decimal('0'),
            'diputacion_ejecutiva': Decimal('0'),
            'diputacion_recargo': Decimal('0'),
            'liquido': Decimal('0'),
            'a_liquidar': Decimal('0')
        }

        # Try to find TOTAL table (usually the first table on last page)
        for idx, table in enumerate(tables):
            if table and len(table) > 0:
                # Check if this is the totals table
                table_text = ' '.join([' '.join([str(cell) for cell in row if cell]) for row in table])
                # Check for LÍQUIDO with or without accent
                has_liquido = 'LIQUIDO' in table_text.upper() or 'LÍQUIDO' in table_text.upper() or 'L�QUIDO' in table_text.upper()
                if 'VOLUNTARIA' in table_text and 'EJECUTIVA' in table_text and has_liquido:
                    # Parse totals from this table
                    # The totals are often in a single cell with newlines, so we need to split
                    for row_idx, row in enumerate(table):
                        if not row:
                            continue

                        # Join all cells in the row and split by newlines to handle multi-line cells
                        for cell_idx, cell in enumerate(row):
                            if not cell:
                                continue

                            # Split by newlines to handle multi-line cells
                            lines = str(cell).split('\n')
                            for line in lines:
                                line = line.strip()
                                if not line:
                                    continue


                                # Match VOLUNTARIA (not DIPUTACIÓN VOLUNTARIA)
                                if line.startswith('VOLUNTARIA'):
                                    match = re.search(r'VOLUNTARIA\s+([\d.,]+)', line)
                                    if match:
                                        totals['voluntaria'] = self._parse_amount(match.group(1))

                                # Match EJECUTIVA (not DIPUTACIÓN EJECUTIVA or TASA EJECUTIVA)
                                elif line.startswith('EJECUTIVA'):
                                    match = re.search(r'EJECUTIVA\s+([\d.,]+)', line)
                                    if match:
                                        totals['ejecutiva'] = self._parse_amount(match.group(1))

                                # Match RECARGO (not DIPUTACIÓN RECARGO)
                                elif line.startswith('RECARGO'):
                                    match = re.search(r'RECARGO\s+([\d.,]+)', line)
                                    if match:
                                        totals['recargo'] = self._parse_amount(match.group(1))

                                # Match DIPUTACIÓN VOLUNTARIA
                                elif 'DIPUTACI' in line.upper() and 'VOLUNTARIA' in line:
                                    match = re.search(r'VOLUNTARIA\s+([\d.,]+)', line)
                                    if match:
                                        totals['diputacion_voluntaria'] = self._parse_amount(match.group(1))

                                # Match DIPUTACIÓN EJECUTIVA
                                elif 'DIPUTACI' in line.upper() and 'EJECUTIVA' in line:
                                    match = re.search(r'EJECUTIVA\s+([\d.,]+)', line)
                                    if match:
                                        totals['diputacion_ejecutiva'] = self._parse_amount(match.group(1))

                                # Match DIPUTACIÓN RECARGO
                                elif 'DIPUTACI' in line.upper() and 'RECARGO' in line:
                                    match = re.search(r'RECARGO\s+([\d.,]+)', line)
                                    if match:
                                        totals['diputacion_recargo'] = self._parse_amount(match.group(1))

                                # Match LÍQUIDO
                                elif re.search(r'L[IÍ]QUIDO', line, re.IGNORECASE):
                                    match = re.search(r'L[IÍ]QUIDO\s+([\d.,]+)', line, re.IGNORECASE)
                                    if match:
                                        totals['liquido'] = self._parse_amount(match.group(1))

        # Extract A LIQUIDAR from text
        match = re.search(r'A\s+LIQUIDAR\s+([\d.,]+)', text)
        if match:
            totals['a_liquidar'] = self._parse_amount(match.group(1))

        # Extract deductions - handle both text format and multiline table cells
        deductions = DeductionDetail()

        # First try to find DEDUCCIONES table and parse multiline cells
        deductions_found = False
        for table in tables:
            if not table:
                continue

            # Check if this is the deductions table
            table_text = ' '.join([str(cell) for row in table for cell in row if cell])
            if 'DEDUCCIONES' in table_text.upper() and 'RECAUDACIÓN' in table_text.upper():
                # Found the deductions table - look for multiline cells
                for row in table:
                    for cell in row:
                        if not cell:
                            continue

                        cell_str = str(cell)
                        # Check if this cell contains deduction details (has newlines and categories)
                        if '\n' in cell_str and 'RECAUDACIÓN' in cell_str:
                            # Parse all lines in this multiline cell
                            lines = cell_str.split('\n')
                            for line in lines:
                                line = line.strip()
                                if not line:
                                    continue

                                # RECAUDACIÓN section
                                if '- TASA VOLUNTARIA' in line:
                                    match = re.search(r'TASA VOLUNTARIA\s+([\d.,]+)', line)
                                    if match:
                                        deductions.tasa_voluntaria = self._parse_amount(match.group(1))
                                        deductions_found = True
                                elif '- TASA EJECUTIVA SIN RECARGO' in line:
                                    match = re.search(r'SIN RECARGO\s+([\d.,]+)', line)
                                    if match:
                                        deductions.tasa_ejecutiva_sin_recargo = self._parse_amount(match.group(1))
                                        deductions_found = True
                                elif '- TASA EJECUTIVA' in line:
                                    match = re.search(r'TASA EJECUTIVA\s+([\d.,]+)', line)
                                    if match:
                                        deductions.tasa_ejecutiva = self._parse_amount(match.group(1))
                                        deductions_found = True
                                elif '- TASA BAJA' in line or 'ÓRGANO GESTOR' in line:
                                    match = re.search(r'([\d.,]+)', line)
                                    if match:
                                        deductions.tasa_baja_organo_gestor_deleg = self._parse_amount(match.group(1))
                                        deductions_found = True

                                # TRIBUTARIA section
                                elif '- TASA GESTIÓN TRIBUTARIA' in line or '- TASA GESTION TRIBUTARIA' in line:
                                    match = re.search(r'TRIBUTARIA\s+([\d.,]+)', line)
                                    if match:
                                        deductions.tasa_gestion_tributaria = self._parse_amount(match.group(1))
                                        deductions_found = True
                                elif '- TASA GESTIÓN CENSAL' in line or '- TASA GESTION CENSAL' in line:
                                    match = re.search(r'CENSAL\s+([\d.,]+)', line)
                                    if match:
                                        deductions.tasa_gestion_censal = self._parse_amount(match.group(1))
                                        deductions_found = True
                                elif '- TASA GESTIÓN CATASTRAL' in line or '- TASA GESTION CATASTRAL' in line:
                                    match = re.search(r'CATASTRAL\s+([\d.,]+)', line)
                                    if match:
                                        deductions.tasa_gestion_catastral = self._parse_amount(match.group(1))
                                        deductions_found = True

                                # MULTAS/SANCIONES section
                                elif '- TASA SANCIÓN TRIBUTARIA' in line or '- TASA SANCION TRIBUTARIA' in line:
                                    match = re.search(r'TRIBUTARIA\s+([\d.,]+)', line)
                                    if match:
                                        deductions.tasa_sancion_tributaria = self._parse_amount(match.group(1))
                                        deductions_found = True
                                elif '- TASA SANCIÓN RECAUDACIÓN' in line or '- TASA SANCION RECAUDACION' in line:
                                    match = re.search(r'RECAUDACIÓN\s+([\d.,]+)', line)
                                    if match:
                                        deductions.tasa_sancion_recaudacion = self._parse_amount(match.group(1))
                                        deductions_found = True
                                elif '- TASA SANCIÓN INSPECCIÓN' in line or '- TASA SANCION INSPECCION' in line:
                                    match = re.search(r'INSPECCIÓN\s+([\d.,]+)', line)
                                    if match:
                                        deductions.tasa_sancion_inspeccion = self._parse_amount(match.group(1))
                                        deductions_found = True
                                elif '- TASA MULTAS DE TRÁFICO' in line or '- TASA MULTAS DE TRAFICO' in line:
                                    match = re.search(r'TRÁFICO\s+([\d.,]+)', line)
                                    if not match:
                                        match = re.search(r'TRAFICO\s+([\d.,]+)', line)
                                    if match:
                                        deductions.tasa_multas_trafico = self._parse_amount(match.group(1))
                                        deductions_found = True

                                # OTRAS DEDUCCIONES section
                                elif '- GASTOS REPERCUTIDOS' in line:
                                    match = re.search(r'REPERCUTIDOS\s+([\d.,]+)', line)
                                    if match:
                                        deductions.gastos_repercutidos = self._parse_amount(match.group(1))
                                        deductions_found = True
                                elif '- ANTICIPOS' in line:
                                    match = re.search(r'ANTICIPOS\s+([\d.,]+)', line)
                                    if match:
                                        deductions.anticipos = self._parse_amount(match.group(1))
                                        deductions_found = True
                                elif '- INTERESES POR ANTICIPO' in line:
                                    match = re.search(r'ANTICIPO\s+([\d.,]+)', line)
                                    if match:
                                        deductions.intereses_por_anticipo = self._parse_amount(match.group(1))
                                        deductions_found = True
                                elif 'EXPEDIENTES COMPENSACIÓN' in line or 'EXPEDIENTES COMPENSACION' in line:
                                    match = re.search(r'([\d.,]+)$', line)
                                    if match:
                                        # Sum both ENTIDAD and TRIBUTARIA into expedientes_compensacion
                                        current = deductions.expedientes_compensacion
                                        deductions.expedientes_compensacion = current + self._parse_amount(match.group(1))
                                        deductions_found = True
                                elif '- EXPEDIENTES INGRESOS INDEBIDOS' in line:
                                    match = re.search(r'INDEBIDOS\s+([\d.,]+)', line)
                                    if match:
                                        deductions.expedientes_ingresos_indebidos = self._parse_amount(match.group(1))
                                        deductions_found = True

        # Fallback: If table parsing didn't work, try regex on full text
        if not deductions_found:
            deduction_patterns = {
                'tasa_voluntaria': r'-?\s*TASA VOLUNTARIA\s+([\d.,]+)',
                'tasa_ejecutiva': r'-?\s*TASA EJECUTIVA(?!\s+SIN)\s+([\d.,]+)',
                'tasa_ejecutiva_sin_recargo': r'-?\s*TASA EJECUTIVA SIN RECARGO\s+([\d.,]+)',
                'tasa_gestion_censal': r'-?\s*TASA GESTIÓN CENSAL\s+([\d.,]+)',
                'tasa_gestion_catastral': r'-?\s*TASA GESTIÓN CATASTRAL\s+([\d.,]+)',
                'tasa_gestion_tributaria': r'-?\s*TASA GESTIÓN TRIBUTARIA\s+([\d.,]+)',
                'tasa_multas_trafico': r'-?\s*TASA MULTAS DE TRÁFICO\s+([\d.,]+)',
                'tasa_sancion_tributaria': r'-?\s*TASA SANCIÓN TRIBUTARIA\s+([\d.,]+)',
                'tasa_sancion_recaudacion': r'-?\s*TASA SANCIÓN RECAUDACIÓN\s+([\d.,]+)',
                'tasa_sancion_inspeccion': r'-?\s*TASA SANCIÓN INSPECCIÓN\s+([\d.,]+)',
                'gastos_repercutidos': r'-?\s*GASTOS REPERCUTIDOS\s+([\d.,]+)',
                'anticipos': r'-?\s*ANTICIPOS\s+([\d.,]+)',
                'intereses_por_anticipo': r'-?\s*INTERESES POR ANTICIPO\s+([\d.,]+)',
                'expedientes_ingresos_indebidos': r'-?\s*EXPEDIENTES INGRESOS INDEBIDOS\s+([\d.,]+)',
            }

            for field, pattern in deduction_patterns.items():
                match = re.search(pattern, text)
                if match:
                    setattr(deductions, field, self._parse_amount(match.group(1)))

        # Extract advance breakdown table
        advance_breakdown = []
        tables = page.extract_tables(table_settings=self.table_settings)
        for table in tables:
            for row in table:
                if row and len(row) >= 8 and str(row[0]).isdigit():
                    try:
                        breakdown = AdvanceBreakdown(
                            ejercicio=int(row[0]),
                            urbana=self._parse_amount(row[1]),
                            rustica=self._parse_amount(row[2]),
                            vehiculos=self._parse_amount(row[3]),
                            bice=self._parse_amount(row[4]),
                            iae=self._parse_amount(row[5]),
                            tasas=self._parse_amount(row[6]),
                            ejecutiva=self._parse_amount(row[7])
                        )
                        advance_breakdown.append(breakdown)
                    except:
                        continue

        return totals, deductions, advance_breakdown

    def _extract_refunds(self, page) -> Tuple[List[RefundRecord], List[RefundSummary]]:
        """Extract refund records and summaries from page 3."""
        refund_records = []
        refund_summaries = []

        tables = page.extract_tables(table_settings=self.table_settings)

        for table in tables:
            for row in table:
                if not row or len(row) < 7:
                    continue

                # Skip headers
                if 'EXPTE' in str(row[0]).upper():
                    continue

                # Check if this is a refund record row (has expediente number)
                if re.match(r'\d{4}/\d+', str(row[0])):
                    try:
                        record = RefundRecord(
                            num_expte=str(row[0]),
                            num_resolucion=str(row[1]),
                            num_solic=int(row[2]) if row[2] and str(row[2]).isdigit() else 0,
                            total_devolucion=self._parse_amount(row[3]),
                            entidad=self._parse_amount(row[4]),
                            diputacion=self._parse_amount(row[5]),
                            intereses=self._parse_amount(row[6]),
                            comp_trib=self._parse_amount(row[7]) if len(row) > 7 else Decimal('0'),
                            a_deducir=self._parse_amount(row[8]) if len(row) > 8 else Decimal('0')
                        )
                        refund_records.append(record)
                    except Exception as e:
                        print(f"Warning: Failed to parse refund record {row}: {e}")
                        continue

                # Check if this is a concept summary row
                elif any(concept in str(row[0]).upper() for concept in ['I.B.I', 'I.V.T.M', 'RUSTICA', 'URBANA']):
                    try:
                        summary = RefundSummary(
                            concepto=str(row[0]).strip(),
                            total_devolucion=self._parse_amount(row[1]) if len(row) > 1 else Decimal('0'),
                            entidad=self._parse_amount(row[2]) if len(row) > 2 else Decimal('0'),
                            diputacion=self._parse_amount(row[3]) if len(row) > 3 else Decimal('0'),
                            intereses=self._parse_amount(row[4]) if len(row) > 4 else Decimal('0')
                        )
                        refund_summaries.append(summary)
                    except:
                        continue

        return refund_records, refund_summaries

    def _parse_amount(self, value: Any) -> Decimal:
        """
        Parse amount from string, handling various formats.

        Examples:
            "1.234,56" -> Decimal("1234.56")
            "1234.56" -> Decimal("1234.56")
            "0,00" -> Decimal("0")
        """
        if value is None or value == '':
            return Decimal('0')

        # Convert to string and clean
        value_str = str(value).strip()

        if not value_str or value_str == '-':
            return Decimal('0')

        # Remove spaces
        value_str = value_str.replace(' ', '')

        # Handle European format (1.234,56) vs American format (1,234.56)
        # If there's both comma and dot, determine which is decimal separator
        if ',' in value_str and '.' in value_str:
            # Find positions
            comma_pos = value_str.rfind(',')
            dot_pos = value_str.rfind('.')

            # The one that comes last is the decimal separator
            if comma_pos > dot_pos:
                # European: 1.234,56
                value_str = value_str.replace('.', '').replace(',', '.')
            else:
                # American: 1,234.56
                value_str = value_str.replace(',', '')
        elif ',' in value_str:
            # Only comma - assume European format
            value_str = value_str.replace('.', '').replace(',', '.')
        # If only dot, keep as is (could be thousands or decimal separator)
        # Assume if dot and 2 digits after, it's decimal

        try:
            return Decimal(value_str)
        except:
            return Decimal('0')


def extract_liquidation_pdf(pdf_path: str, table_settings: Optional[Dict[str, Any]] = None) -> LiquidationDocument:
    """
    Convenience function to extract a liquidation PDF.

    Args:
        pdf_path: Path to PDF file
        table_settings: Optional dictionary of pdfplumber table extraction settings

    Returns:
        Extracted LiquidationDocument
    """
    extractor = LiquidationPDFExtractor(pdf_path, table_settings=table_settings)
    return extractor.extract()

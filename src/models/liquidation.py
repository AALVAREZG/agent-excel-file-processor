"""
Data models for liquidation documents (Documentos de Liquidación).
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Dict
from datetime import date


@dataclass
class TributeRecord:
    """
    Represents a single tribute charge record from Excel data.

    Excel columns mapping:
    - C_EJERCICIO: contable year
    - C_CONCEPTO: concepto name
    - CLAVE_C: contable key
    - CLAVE_R: recaudatory key
    - C_CARGO: pending amount on init
    - C_DATAS: amount to null
    - C_VOLUNTARIA: amount recaudated in voluntaria phase
    - C_EJECUTIVA: amount recaudated in ejecutiva phase
    - CC_PENDIENTE: pending amount to pass to next contable year
    - C_TOTAL: calculated as C_VOLUNTARIA + C_EJECUTIVA
    """
    ejercicio: int  # C_EJERCICIO - Fiscal year
    concepto: str  # C_CONCEPTO - Concept name
    clave_contabilidad: str  # CLAVE_C - Accounting code
    clave_recaudacion: str  # CLAVE_R - Collection code
    c_cargo: Decimal  # C_CARGO - Pending amount on init
    c_datas: Decimal  # C_DATAS - Amount to null
    c_voluntaria: Decimal  # C_VOLUNTARIA - Amount recaudated in voluntaria phase
    c_ejecutiva: Decimal  # C_EJECUTIVA - Amount recaudated in ejecutiva phase
    cc_pendiente: Decimal  # CC_PENDIENTE - Pending amount to pass to next year

    def __post_init__(self):
        """Convert string amounts to Decimal if needed."""
        for field_name in ['c_cargo', 'c_datas', 'c_voluntaria', 'c_ejecutiva', 'cc_pendiente']:
            value = getattr(self, field_name)
            if not isinstance(value, Decimal):
                setattr(self, field_name, Decimal(str(value)))

    @property
    def c_total(self) -> Decimal:
        """Calculate C_TOTAL as C_VOLUNTARIA + C_EJECUTIVA."""
        return self.c_voluntaria + self.c_ejecutiva


@dataclass
class ExerciseSummary:
    """
    Summary of amounts by fiscal year (exercise).
    """
    ejercicio: int
    c_cargo: Decimal
    c_datas: Decimal
    c_voluntaria: Decimal
    c_ejecutiva: Decimal
    cc_pendiente: Decimal
    records: List[TributeRecord] = field(default_factory=list)

    @property
    def c_total(self) -> Decimal:
        """Calculate C_TOTAL as C_VOLUNTARIA + C_EJECUTIVA."""
        return self.c_voluntaria + self.c_ejecutiva


@dataclass
class ExerciseValidationResult:
    """
    Validation result for a specific fiscal year.
    Contains comparison between calculated totals and documented summary.
    """
    ejercicio: int
    is_valid: bool
    # Calculated values (from summing tribute records)
    calc_c_cargo: Decimal
    calc_c_datas: Decimal
    calc_c_voluntaria: Decimal
    calc_c_ejecutiva: Decimal
    calc_cc_pendiente: Decimal
    calc_c_total: Decimal
    # Documented values (from ExerciseSummary)
    doc_c_cargo: Decimal
    doc_c_datas: Decimal
    doc_c_voluntaria: Decimal
    doc_c_ejecutiva: Decimal
    doc_cc_pendiente: Decimal
    doc_c_total: Decimal
    # Error messages if validation fails
    errors: List[str] = field(default_factory=list)


# PDF-specific dataclasses removed - not needed for Excel input format
# DeductionDetail, AdvanceBreakdown, RefundRecord, RefundSummary


@dataclass
class LiquidationDocument:
    """
    Complete liquidation document with all sections.
    Adapted for Excel input data format.
    """
    # Header information
    ejercicio: int
    entidad: str = ""  # Entity (municipality)

    # Main records
    tribute_records: List[TributeRecord] = field(default_factory=list)

    # Summaries by exercise
    exercise_summaries: List[ExerciseSummary] = field(default_factory=list)

    # Overall totals
    total_c_cargo: Decimal = Decimal('0')
    total_c_datas: Decimal = Decimal('0')
    total_c_voluntaria: Decimal = Decimal('0')
    total_c_ejecutiva: Decimal = Decimal('0')
    total_cc_pendiente: Decimal = Decimal('0')

    @property
    def total_c_total(self) -> Decimal:
        """Calculate total C_TOTAL as sum of C_VOLUNTARIA + C_EJECUTIVA."""
        return self.total_c_voluntaria + self.total_c_ejecutiva

    def validate_totals(self) -> List[str]:
        """
        Validate that totals match the sum of records.
        Returns list of validation errors (empty if valid).
        """
        errors = []

        # Calculate sum from records
        calc_c_cargo = sum(r.c_cargo for r in self.tribute_records)
        calc_c_datas = sum(r.c_datas for r in self.tribute_records)
        calc_c_voluntaria = sum(r.c_voluntaria for r in self.tribute_records)
        calc_c_ejecutiva = sum(r.c_ejecutiva for r in self.tribute_records)
        calc_cc_pendiente = sum(r.cc_pendiente for r in self.tribute_records)
        calc_c_total = sum(r.c_total for r in self.tribute_records)

        tolerance = Decimal('0.01')  # Allow 1 cent tolerance for rounding

        if abs(calc_c_cargo - self.total_c_cargo) > tolerance:
            errors.append(f"C_CARGO mismatch: calculated {calc_c_cargo} vs documented {self.total_c_cargo}")

        if abs(calc_c_datas - self.total_c_datas) > tolerance:
            errors.append(f"C_DATAS mismatch: calculated {calc_c_datas} vs documented {self.total_c_datas}")

        if abs(calc_c_voluntaria - self.total_c_voluntaria) > tolerance:
            errors.append(f"C_VOLUNTARIA mismatch: calculated {calc_c_voluntaria} vs documented {self.total_c_voluntaria}")

        if abs(calc_c_ejecutiva - self.total_c_ejecutiva) > tolerance:
            errors.append(f"C_EJECUTIVA mismatch: calculated {calc_c_ejecutiva} vs documented {self.total_c_ejecutiva}")

        if abs(calc_cc_pendiente - self.total_cc_pendiente) > tolerance:
            errors.append(f"CC_PENDIENTE mismatch: calculated {calc_cc_pendiente} vs documented {self.total_cc_pendiente}")

        if abs(calc_c_total - self.total_c_total) > tolerance:
            errors.append(f"C_TOTAL mismatch: calculated {calc_c_total} vs documented {self.total_c_total}")

        return errors

    def validate_exercise_summaries(self) -> Dict[int, 'ExerciseValidationResult']:
        """
        Validate that per-year totals match their exercise summaries.

        Returns:
            Dictionary mapping ejercicio (year) to ExerciseValidationResult
        """
        from src.models.liquidation import ExerciseValidationResult

        results = {}
        tolerance = Decimal('0.01')  # Allow 1 cent tolerance for rounding

        for summary in self.exercise_summaries:
            ejercicio = summary.ejercicio
            year_records = self.get_records_by_year(ejercicio)

            # Calculate totals from tribute records for this year
            calc_c_cargo = sum(r.c_cargo for r in year_records)
            calc_c_datas = sum(r.c_datas for r in year_records)
            calc_c_voluntaria = sum(r.c_voluntaria for r in year_records)
            calc_c_ejecutiva = sum(r.c_ejecutiva for r in year_records)
            calc_cc_pendiente = sum(r.cc_pendiente for r in year_records)
            calc_c_total = sum(r.c_total for r in year_records)

            # Check for discrepancies
            errors = []
            is_valid = True

            if abs(calc_c_cargo - summary.c_cargo) > tolerance:
                errors.append(f"C_CARGO: calculado {calc_c_cargo} vs documentado {summary.c_cargo}")
                is_valid = False

            if abs(calc_c_datas - summary.c_datas) > tolerance:
                errors.append(f"C_DATAS: calculado {calc_c_datas} vs documentado {summary.c_datas}")
                is_valid = False

            if abs(calc_c_voluntaria - summary.c_voluntaria) > tolerance:
                errors.append(f"C_VOLUNTARIA: calculado {calc_c_voluntaria} vs documentado {summary.c_voluntaria}")
                is_valid = False

            if abs(calc_c_ejecutiva - summary.c_ejecutiva) > tolerance:
                errors.append(f"C_EJECUTIVA: calculado {calc_c_ejecutiva} vs documentado {summary.c_ejecutiva}")
                is_valid = False

            if abs(calc_cc_pendiente - summary.cc_pendiente) > tolerance:
                errors.append(f"CC_PENDIENTE: calculado {calc_cc_pendiente} vs documentado {summary.cc_pendiente}")
                is_valid = False

            if abs(calc_c_total - summary.c_total) > tolerance:
                errors.append(f"C_TOTAL: calculado {calc_c_total} vs documentado {summary.c_total}")
                is_valid = False

            # Create validation result
            result = ExerciseValidationResult(
                ejercicio=ejercicio,
                is_valid=is_valid,
                calc_c_cargo=calc_c_cargo,
                calc_c_datas=calc_c_datas,
                calc_c_voluntaria=calc_c_voluntaria,
                calc_c_ejecutiva=calc_c_ejecutiva,
                calc_cc_pendiente=calc_cc_pendiente,
                calc_c_total=calc_c_total,
                doc_c_cargo=summary.c_cargo,
                doc_c_datas=summary.c_datas,
                doc_c_voluntaria=summary.c_voluntaria,
                doc_c_ejecutiva=summary.c_ejecutiva,
                doc_cc_pendiente=summary.cc_pendiente,
                doc_c_total=summary.c_total,
                errors=errors
            )

            results[ejercicio] = result

        return results

    def get_records_by_concept(self, concepto: str) -> List[TributeRecord]:
        """Get all records for a specific concept."""
        return [r for r in self.tribute_records if r.concepto == concepto]

    def get_records_by_year(self, ejercicio: int) -> List[TributeRecord]:
        """Get all records for a specific fiscal year."""
        return [r for r in self.tribute_records if r.ejercicio == ejercicio]

    @property
    def total_records(self) -> int:
        """Total number of tribute records."""
        return len(self.tribute_records)

    @property
    def has_exercise_validation_errors(self) -> bool:
        """Check if any exercise summary has validation errors."""
        validation_results = self.validate_exercise_summaries()
        return any(not result.is_valid for result in validation_results.values())

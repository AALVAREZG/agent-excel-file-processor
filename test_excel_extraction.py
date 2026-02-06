"""
Test script to validate Excel extraction functionality.
"""
from src.extractors.excel_extractor import extract_recaudation_excel
from pathlib import Path

def test_excel_extraction():
    """Test extracting data from Excel file."""
    excel_path = "data/CTA_2025_026.xlsx"

    if not Path(excel_path).exists():
        print(f"ERROR: File not found: {excel_path}")
        return False

    print("=" * 80)
    print("TESTING EXCEL EXTRACTION")
    print("=" * 80)
    print(f"\nReading file: {excel_path}")

    try:
        # Extract document
        doc = extract_recaudation_excel(excel_path)

        print(f"\n[OK] Extraction successful!")
        print(f"\nDocument Information:")
        print(f"  - Entity: {doc.entidad}")
        print(f"  - Code: {doc.codigo_entidad}")
        print(f"  - Year: {doc.ejercicio}")
        print(f"  - Liquidation #: {doc.numero_liquidacion}")

        print(f"\nTribute Records:")
        print(f"  - Total records: {len(doc.tribute_records)}")
        if doc.tribute_records:
            first_record = doc.tribute_records[0]
            print(f"  - First record:")
            print(f"      Concept: {first_record.concepto}")
            print(f"      Year: {first_record.ejercicio}")
            print(f"      Voluntary: {first_record.voluntaria:,.2f}")
            print(f"      Executive: {first_record.ejecutiva:,.2f}")
            print(f"      Liquid: {first_record.liquido:,.2f}")

        print(f"\nExercise Summaries:")
        print(f"  - Total years: {len(doc.exercise_summaries)}")
        for summary in doc.exercise_summaries:
            print(f"  - Year {summary.ejercicio}:")
            print(f"      Records: {len(summary.records)}")
            print(f"      Voluntary: {summary.voluntaria:,.2f}")
            print(f"      Executive: {summary.ejecutiva:,.2f}")
            print(f"      Liquid: {summary.liquido:,.2f}")

        print(f"\nGlobal Totals:")
        print(f"  - Total Voluntary: {doc.total_voluntaria:,.2f}")
        print(f"  - Total Executive: {doc.total_ejecutiva:,.2f}")
        print(f"  - Total Liquid: {doc.total_liquido:,.2f}")

        # Validate totals
        print(f"\nValidation:")
        errors = doc.validate_totals()
        if errors:
            print(f"  [WARNING] Validation errors found:")
            for error in errors:
                print(f"    - {error}")
        else:
            print(f"  [OK] All totals validated successfully!")

        print("\n" + "=" * 80)
        print("TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n[ERROR] Extraction failed!")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_excel_extraction()
    exit(0 if success else 1)

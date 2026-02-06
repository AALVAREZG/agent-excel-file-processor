"""
HTML Exporter for Grouped Concept Records
Exports liquidation data grouped by concept to a standalone HTML page
"""

from typing import List, Dict, Tuple, Set
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from ..models.liquidation import LiquidationDocument, TributeRecord
from ..models.grouping_config import GroupingConfig


class HTMLGroupedExporter:
    """Exports grouped concept records to HTML format"""

    # Mapping of OPAEF concept codes to local contable partidas
    CORRESP_PARTIDAS = {
        '751': ['300', 'agua'],  # consumo agua
        '678': ['300', 'agua'],  # agua alta contador
        '450': ['300', 'agua'],  # agua consumo
        '451': ['10049', 'agua'],  # iva agua?
        '452': ['300', 'agua'],  # agua canon ayto
        '750': ['300', 'agua'],  # agua cuota fija
        '568': ['305', 'agua'],  # agua canon junta andalucía
        '573': ['10049', 'agua'],  # agua iva cuota fija
        '665': ['10049', 'agua'],  # agua iva agua
        '752': ['10049', 'agua'],  # agua iva
        '753': ['10049', 'agua'],  # agua iva conservacion
        '015': ['116', 'plusvalia'],  # plusvalia ivtnu
        '022': ['302', 'basuras'],  # basuras
        '025': ['331', 'cocheras'],  # entr. vehículos
        '033': ['325', 'exp. doc.'],  # licencia apertura
        '520': ['325', 'exp. doc.'],  # licencia apertura2
        '039': ['32903', 'mercado'],  # mercado
        '062': ['339', 'dom. publico'],  # ocup. via pública
        '640': ['339', 'dom. publico'],  # tasas ocup dom publico (barraca feria)
        '649': ['339', 'dom. publico'],  # tasas ocup dom publico (andamios/esco)
        '663': ['339', 'dom. publico'],  # tasas ocup dom publico (escombros)
        '329': ['331', 'cocheras'],  # reserva aparcamiento
        '008': ['32900', 'cementerio'],  # TASAS CEMENTERIO INHUMACION
        '035': ['32900', 'cementerio'],  # serv. cementerio
        '372': ['32904', 'guarderia'],  # guardería
        '398': ['32904', 'guarderia'],  # guardería comedor
        '516': ['32904', 'guarderia'],  # taller absentismo
        '806': ['332', 'topv'],  # topv vuelo, suelo, sub, emp suministradoras
        '462': ['39120', 'multas ant'],  # multas trafico antiguas
        '512': ['290', 'obras'],  # impuesto de constr, instalaciones y obras
        '699': ['290', 'obras'],  # prestacion compensatoria ley ou
        '669': ['399', '399 otros_i'],  # daños via publica
        # GESTION OPAEF
        '102': ['114', 'ibi esp'],  # IBI INMEBLES ESPECIALES
        '204': ['130', 'iae'],  # iae
        '206': ['130', 'iae'],  # altas iae
        '205': ['112', 'ibi rus'],  # ibi rústica
        '208': ['113', 'ibi urb'],  # ibi urbana
        '213': ['130', 'iae inspeccion'],  # iae inspeccion
        '218': ['39110', 'multas por infracc trib'],  # multas por infracciones tributarias
        '501': ['115', 'ivtm'],  # ivtm
        '700': ['393', 'intereses'],  # intereses de demora
        '777': ['39120', 'multas'],  # multas tráfico
    }

    def __init__(self, document: LiquidationDocument, grouping_config: GroupingConfig):
        """
        Initialize the HTML exporter

        Args:
            document: LiquidationDocument with all records
            grouping_config: GroupingConfig with concept and custom group definitions
        """
        self.document = document
        self.grouping_config = grouping_config

    def _compact_codes(self, codes: List[str]) -> str:
        """
        Compact a list of codes by grouping common patterns.

        Examples:
            2021.58.064.573, 2021.58.064.665
            -> 026/2021/58/{064}/573,665

            2023.E.0000783, 2023.E.0000784
            -> 2023/E/783,784
        """
        if not codes:
            return ""
        print("Codes to compact:", codes)
        # {(year, level): {sublevel: {suffixes}}}
        four_part = defaultdict(lambda: defaultdict(set))
        e_codes = defaultdict(list)  # {(year, alpha): [nums]}
        otros = []

        for c in codes:
            parts = c.split('.')

            # Format: 2021.58.064.573
            if len(parts) == 4 and parts[1].isdigit():
                year, level, sublevel, suffix = parts
                four_part[(year, level)][sublevel].add(suffix)

            # Format: 2023.E.0000783
            elif len(parts) == 3 and parts[1].isalpha() and len(parts[1]) == 1:
                year = parts[0]
                alpha = parts[1]
                num = parts[2].lstrip('0') or '0'
                e_codes[(year, alpha)].append(num)

            else:
                otros.append(c)

        result = []

        # Format four-part codes
        for (year, level), sublevels_dict in sorted(four_part.items()):
            sublevels = sorted(sublevels_dict.keys())

            all_suffixes = set()
            for suffixes in sublevels_dict.values():
                all_suffixes.update(suffixes)

            sublevels_str = '{' + ','.join(sublevels) + '}'
            suffixes_str = ','.join(sorted(all_suffixes))

            result.append(f"{year}.{level}.{sublevels_str}.{suffixes_str}")

        # Format E-codes (or any single-letter codes)
        for (year, alpha), nums in sorted(e_codes.items()):
            sorted_nums = sorted(nums, key=lambda x: int(x) if x.isdigit() else 0)
            result.append(f"{year}.{alpha}.{','.join(sorted_nums)}")

        # Add unrecognized codes
        result.extend(otros)
        print("Compacted codes result:", result)
        return ' '.join(result)


    def _compact_codes_old_pdf(self, codes: List[str]) -> str:
        """
        Compact a list of codes by grouping common patterns.

        Examples:
            026/2021/58/064/573, 026/2021/58/064/665, ...
            -> 026/2021/58/{064,068,086}/573,665,752,753

            2023/E/0000783, 2023/E/0000784, ...
            -> 2023/E/783,784,786,787

        Args:
            codes: List of code strings to compact

        Returns:
            Compacted string representation
        """
        if not codes:
            return ""

        # Group codes by pattern
        five_part = defaultdict(lambda: defaultdict(set))  # {(base): {level: {suffixes}}}
        e_codes = []
        otros = []

        for c in codes:
            parts = c.split('/')
            if len(parts) == 5:
                # Format: 026/2021/58/064/573
                base = tuple(parts[:3])  # (026, 2021, 58)
                level = parts[3]  # 064
                suffix = parts[4]  # 573
                five_part[base][level].add(suffix)
            elif len(parts) == 3 and parts[1] == 'E':
                # Format: 2023/E/0000783
                # Remove leading zeros from number
                num = parts[2].lstrip('0') or '0'
                e_codes.append(num)
            else:
                # Unknown format, keep as-is
                otros.append(c)

        result = []

        # Format five-part codes
        for base, levels_dict in sorted(five_part.items()):
            levels = sorted(levels_dict.keys())
            # Get all unique suffixes across all levels
            all_suffixes = set()
            for suffixes in levels_dict.values():
                all_suffixes.update(suffixes)
            suffixes_str = ','.join(sorted(all_suffixes))

            # Format: 026/2021/58/{064,068,086}/573,665,752,753
            base_str = '/'.join(base)
            levels_str = '{' + ','.join(levels) + '}'
            result.append(f"{base_str}/{levels_str}/{suffixes_str}")

        # Format E-codes (sort numerically)
        if e_codes:
            # Sort numerically
            sorted_e = sorted(e_codes, key=lambda x: int(x) if x.isdigit() else 0)
            result.append(f"2023/E/{','.join(sorted_e)}")

        # Add other codes as-is
        result.extend(otros)

        return ' '.join(result)

    def _get_partidas_from_records(self, records: List[TributeRecord]) -> str:
        """
        Extract unique partidas from records and format them.

        Args:
            records: List of tribute records

        Returns:
            Formatted string with partidas, e.g., "300, 10049"
        """
        partidas_set = set()

        for record in records:
            # Extract concept code from clave_recaudacion
            concept_code = self.grouping_config.get_concept_code(record.clave_recaudacion)

            # Look up partida in the mapping
            if concept_code in self.CORRESP_PARTIDAS:
                partida = self.CORRESP_PARTIDAS[concept_code][0]
                partidas_set.add(partida)

        # Return sorted unique partidas as comma-separated string
        if partidas_set:
            return ', '.join(sorted(partidas_set))
        else:
            # If no partidas found, return a default value
            return 'N/A'

    def export_grouped_concepts(
        self,
        output_path: str,
        group_by_year: bool = True,
        group_by_concept: bool = True,
        group_by_custom: bool = False
    ) -> None:
        """
        Export grouped concept records to HTML

        Args:
            output_path: Path where to save the HTML file
            group_by_year: Whether to group by year
            group_by_concept: Whether to group by concept
            group_by_custom: Whether to apply custom grouping
        """
        # Organize data according to grouping settings
        grouped_data = self._organize_data(group_by_year, group_by_concept, group_by_custom)

        # Generate HTML content
        html_content = self._generate_html(grouped_data, group_by_year, group_by_concept, group_by_custom)

        # Write to file
        output_file = Path(output_path)
        output_file.write_text(html_content, encoding='utf-8')

    def _organize_data(
        self,
        group_by_year: bool,
        group_by_concept: bool,
        group_by_custom: bool
    ) -> Dict:
        """
        Organize records according to grouping configuration

        Returns:
            Dictionary with organized data structure
        """
        if group_by_year:
            # Group by year first
            years_data = {}
            for year in sorted(set(r.ejercicio for r in self.document.tribute_records)):
                year_records = [r for r in self.document.tribute_records if r.ejercicio == year]
                years_data[year] = self._organize_records(year_records, group_by_concept, group_by_custom)
            return years_data
        else:
            # All records together
            return {None: self._organize_records(self.document.tribute_records, group_by_concept, group_by_custom)}

    def _organize_records(
        self,
        records: List[TributeRecord],
        group_by_concept: bool,
        group_by_custom: bool
    ) -> List[Dict]:
        """
        Organize a list of records into groups

        Returns:
            List of group dictionaries with name, records, and totals
        """
        if not group_by_concept and not group_by_custom:
            # Return all records as one group
            return [{
                'name': 'Todos los conceptos',
                'records': records,
                'c_total': sum(r.c_total for r in records)
            }]

        groups = []

        if group_by_concept and not group_by_custom:
            # Group by concept only
            concept_groups = {}
            for record in records:
                concept_code = self.grouping_config.get_concept_code(record.clave_recaudacion)
                concept_name = self.grouping_config.concept_names.get(concept_code, concept_code)

                if concept_name not in concept_groups:
                    concept_groups[concept_name] = []
                concept_groups[concept_name].append(record)

            for concept_name, concept_records in sorted(concept_groups.items()):
                groups.append({
                    'name': concept_name,
                    'records': concept_records,
                    'c_total': sum(r.c_total for r in concept_records)
                })

        elif group_by_custom:
            # Apply custom grouping
            if group_by_concept:
                # First group by concept, then apply custom groups
                concept_groups = {}
                for record in records:
                    concept_code = self.grouping_config.get_concept_code(record.clave_recaudacion)
                    if concept_code not in concept_groups:
                        concept_groups[concept_code] = []
                    concept_groups[concept_code].append(record)

                # Apply custom groups to concepts
                used_concepts = set()
                for custom_group in self.grouping_config.custom_groups:
                    group_records = []
                    for concept_code in custom_group.concept_codes:
                        if concept_code in concept_groups:
                            group_records.extend(concept_groups[concept_code])
                            used_concepts.add(concept_code)

                    if group_records:
                        groups.append({
                            'name': custom_group.name,
                            'records': group_records,
                            'c_total': sum(r.c_total for r in group_records)
                        })

                # Add ungrouped concepts
                for concept_code, concept_records in sorted(concept_groups.items()):
                    if concept_code not in used_concepts:
                        concept_name = self.grouping_config.concept_names.get(concept_code, concept_code)
                        groups.append({
                            'name': concept_name,
                            'records': concept_records,
                            'c_total': sum(r.c_total for r in concept_records)
                        })
            else:
                # Apply custom groups directly to records
                used_records = set()
                for custom_group in self.grouping_config.custom_groups:
                    group_records = []
                    for record in records:
                        concept_code = self.grouping_config.get_concept_code(record.clave_recaudacion)
                        if concept_code in custom_group.concept_codes:
                            group_records.append(record)
                            used_records.add(id(record))

                    if group_records:
                        groups.append({
                            'name': custom_group.name,
                            'records': group_records,
                            'c_total': sum(r.c_total for r in group_records)
                        })

                # Add ungrouped records
                ungrouped_records = [r for r in records if id(r) not in used_records]
                if ungrouped_records:
                    groups.append({
                        'name': 'Sin agrupar',
                        'records': ungrouped_records,
                        'c_total': sum(r.c_total for r in ungrouped_records)
                    })

        return groups

    def _collect_unique_claves(self, records: List[TributeRecord]) -> Tuple[str, str]:
        """
        Collect unique clave_recaudacion and clave_contabilidad from records
        and compact them using the _compact_codes method.

        Returns:
            Tuple of (claves_recaudacion_str, claves_contabilidad_str)
        """
        claves_recaudacion = sorted(set(r.clave_recaudacion for r in records))
        claves_contabilidad = sorted(set(r.clave_contabilidad for r in records))

        # Compact the codes
        compacted_recaudacion = self._compact_codes(claves_recaudacion)
        compacted_contabilidad = self._compact_codes(claves_contabilidad)

        return compacted_recaudacion, compacted_contabilidad

    def _build_texto_sical(self, ejercicio: int, group_name: str, records: List[TributeRecord]) -> str:
        """
        Build the texto SICAL string for a group

        Format: OPAEF. REGULARIZACION COBROS {ejercicio} - {nombre_grupo} {claves_rec} {claves_cont}

        Args:
            ejercicio: Fiscal year
            group_name: Name of the group
            records: List of tribute records for this group

        Returns:
            Formatted texto SICAL string
        """
        claves_rec, claves_cont = self._collect_unique_claves(records)

        # Build the texto with ejercicio and group name
        return (
            f"OPAEF. REGULARIZACION COBROS {ejercicio} - {group_name} "
            f"{claves_rec} {claves_cont}"
        )

    def _format_decimal(self, value: Decimal) -> str:
        """Format decimal value as currency string"""
        return f"{value:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.')

    def _generate_html(
        self,
        grouped_data: Dict,
        group_by_year: bool,
        group_by_concept: bool,
        group_by_custom: bool
    ) -> str:
        """Generate complete HTML document"""

        # Build the HTML content
        html_parts = [
            self._html_header(),
            self._html_document_info(),
        ]

        # Generate tables for each year (or single table if not grouped by year)
        for year, groups in grouped_data.items():
            html_parts.append(self._html_year_table(year, groups))

        html_parts.append(self._html_footer())

        return '\n'.join(html_parts)

    def _html_header(self) -> str:
        """Generate HTML header with CSS and JavaScript"""
        return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Liquidación OPAEF - Agrupación por Conceptos</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            color: #2E3440;
            padding: 20px;
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }

        .header {
            background: linear-gradient(135deg, #366092 0%, #3A5F7D 100%);
            color: white;
            padding: 25px;
            border-radius: 8px 8px 0 0;
            margin: -30px -30px 30px -30px;
        }

        .header h1 {
            font-size: 24px;
            margin-bottom: 15px;
            display: inline-block;
        }

        .print-btn {
            background-color: white;
            color: #366092;
            border: 2px solid white;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            float: right;
            transition: all 0.2s;
        }

        .print-btn:hover {
            background-color: #f0f0f0;
            transform: translateY(-1px);
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }

        .doc-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
            padding: 20px;
            background-color: #EEF3F7;
            border-radius: 6px;
        }

        .doc-info-item {
            display: flex;
            flex-direction: column;
        }

        .doc-info-label {
            font-weight: bold;
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 5px;
        }

        .doc-info-value {
            font-size: 16px;
            color: #2E3440;
        }

        .year-section {
            margin-bottom: 40px;
        }

        .print-year-header {
            display: none;
        }

        .year-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .year-header {
            background: linear-gradient(135deg, #3A5F7D 0%, #366092 100%);
            color: white;
            text-align: left;
            padding: 15px 20px;
            font-size: 18px;
            font-weight: bold;
        }

        .year-table tbody tr {
            border-bottom: 1px solid #d0d0d0;
        }

        .year-table td {
            padding: 12px 15px;
            vertical-align: middle;
        }

        .label-cell {
            font-weight: bold;
            background-color: #D6E4F0;
            color: #2E3440;
            width: 150px;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
        }

        .value-cell {
            background-color: white;
        }

        .group-separator {
            height: 20px;
            background-color: #f5f5f5;
        }

        .footer-row {
            background: linear-gradient(135deg, #D9E1F2 0%, #D6E4F0 100%);
            font-weight: bold;
            font-size: 16px;
        }

        .footer-row td {
            padding: 15px 20px;
        }

        .copy-btn {
            background-color: #366092;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-left: 10px;
            transition: all 0.2s;
        }

        .copy-btn:hover {
            background-color: #2a4d75;
            transform: translateY(-1px);
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }

        .copy-btn:active {
            transform: translateY(0);
        }

        .copy-btn.copied {
            background-color: #2E7D32;
        }

        .copy-btn.copied::after {
            content: " ✓";
        }

        .texto-sical {
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #2E3440;
            word-break: break-word;
        }

        .amount {
            font-weight: bold;
            color: #2E7D32;
            font-size: 15px;
            text-align: right;
        }

        @media print {
            body {
                background-color: white;
                padding: 0;
                margin: 0;
            }

            .container {
                box-shadow: none;
                padding: 15px;
                max-width: 100%;
            }

            .header {
                background: #366092 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                margin: -15px -15px 20px -15px !important;
                padding: 15px !important;
                border-radius: 0 !important;
            }

            .print-btn {
                display: none;
            }

            .copy-btn {
                display: none;
            }

            .header,
            .doc-info {
                display: none;
            }

            .print-year-header {
                display: block !important;
                background-color: #EEF3F7 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                padding: 15px;
                margin-bottom: 15px;
                border: 1px solid #ccc;
            }

            .print-year-header h2 {
                background: #366092 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                color: white !important;
                padding: 10px;
                margin: -15px -15px 10px -15px;
                font-size: 18px;
            }

            .print-doc-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
                font-size: 11px;
            }

            .print-doc-item {
                display: flex;
                flex-direction: column;
            }

            .print-doc-label {
                font-weight: bold;
                font-size: 9px;
                color: #666;
                text-transform: uppercase;
                margin-bottom: 2px;
            }

            .print-doc-value {
                font-size: 11px;
                color: #2E3440;
            }

            .year-section {
                page-break-before: always;
                page-break-inside: avoid;
                margin-top: 0;
            }

            .year-header {
                background: #3A5F7D !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }

            .label-cell {
                background-color: #D6E4F0 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }

            .footer-row {
                background: #D9E1F2 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }

            .group-separator {
                background-color: #f5f5f5 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }

            /* Repeat document info on each page */
            .doc-info {
                display: block;
                position: running(docinfo);
            }

            @page {
                margin: 1.5cm;
                size: A4;
            }

            /* Ensure proper spacing */
            .year-table {
                margin-bottom: 10px;
            }

            .texto-sical {
                font-size: 11px;
            }

            .year-table td {
                padding: 8px 10px;
            }
        }

        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }

            .header {
                margin: -15px -15px 20px -15px;
                padding: 15px;
            }

            .doc-info {
                grid-template-columns: 1fr;
            }

            .year-table td {
                font-size: 12px;
                padding: 8px 10px;
            }

            .texto-sical {
                font-size: 11px;
            }
        }
    </style>
    <script>
        function copyToClipboard(text, buttonId) {
            navigator.clipboard.writeText(text).then(function() {
                // Visual feedback
                const button = document.getElementById(buttonId);
                button.classList.add('copied');
                button.textContent = 'Copiado';

                setTimeout(function() {
                    button.classList.remove('copied');
                    button.textContent = 'Copiar';
                }, 2000);
            }).catch(function(err) {
                console.error('Error al copiar: ', err);
                alert('No se pudo copiar al portapapeles');
            });
        }

        function printReport() {
            window.print();
        }
    </script>
</head>
<body>
    <div class="container">
'''

    def _html_document_info(self) -> str:
        """Generate document information section"""
        return f'''
        <div class="header">
            <h1>Liquidación OPAEF - Agrupación por Conceptos</h1>
            <button class="print-btn" onclick="printReport()">🖨️ Imprimir</button>
        </div>

        <div class="doc-info">
            <div class="doc-info-item">
                <div class="doc-info-label">Entidad</div>
                <div class="doc-info-value">{self.document.entidad}</div>
            </div>
            <div class="doc-info-item">
                <div class="doc-info-label">Ejercicio</div>
                <div class="doc-info-value">{self.document.ejercicio}</div>
            </div>
            <div class="doc-info-item">
                <div class="doc-info-label">Fecha Exportación</div>
                <div class="doc-info-value">{datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
            </div>
        </div>
'''

    def _html_year_table(self, year: int, groups: List[Dict]) -> str:
        """Generate HTML table for a year's groups"""
        year_label = f"Ejercicio {year}" if year else "Todos los ejercicios"

        # Calculate total for footer
        total_c_total = sum(g['c_total'] for g in groups)

        # Format document info for print header
        fecha_export_str = datetime.now().strftime('%d/%m/%Y %H:%M')

        html_parts = [f'''
        <div class="year-section">
            <div class="print-year-header">
                <h2>Liquidación OPAEF - Agrupación por Conceptos</h2>
                <div class="print-doc-grid">
                    <div class="print-doc-item">
                        <div class="print-doc-label">Entidad</div>
                        <div class="print-doc-value">{self.document.entidad}</div>
                    </div>
                    <div class="print-doc-item">
                        <div class="print-doc-label">Ejercicio</div>
                        <div class="print-doc-value">{year}</div>
                    </div>
                    <div class="print-doc-item">
                        <div class="print-doc-label">Fecha Exportación</div>
                        <div class="print-doc-value">{fecha_export_str}</div>
                    </div>
                </div>
            </div>
            <table class="year-table">
                <thead>
                    <tr>
                        <th colspan="2" class="year-header">{year_label}</th>
                    </tr>
                </thead>
                <tbody>
''']

        # Generate rows for each group
        for idx, group in enumerate(groups):
            group_id = f"group_{year}_{idx}"
            # Use the year if available, otherwise use the document's ejercicio
            ejercicio = year if year is not None else self.document.ejercicio
            texto_sical = self._build_texto_sical(ejercicio, group['name'], group['records'])
            c_total_formatted = self._format_decimal(group['c_total'])
            # Get partidas for this group
            partidas = self._get_partidas_from_records(group['records'])

            # Row 1: Grupo and Texto SICAL
            html_parts.append(f'''
                    <tr>
                        <td class="label-cell">Grupo</td>
                        <td class="value-cell"><strong>{group['name']}</strong></td>
                    </tr>
                    <tr>
                        <td class="label-cell">Texto SICAL</td>
                        <td class="value-cell">
                            <span class="texto-sical">{texto_sical}</span>
                            <button class="copy-btn" id="btn_sical_{group_id}" onclick="copyToClipboard('{self._escape_js(texto_sical)}', 'btn_sical_{group_id}')">Copiar</button>
                        </td>
                    </tr>
                    <tr>
                        <td class="label-cell">Aplicación</td>
                        <td class="value-cell">{partidas}</td>
                    </tr>
                    <tr>
                        <td class="label-cell">Importe Total</td>
                        <td class="value-cell">
                            <span class="amount">{c_total_formatted}</span>
                            <button class="copy-btn" id="btn_amount_{group_id}" onclick="copyToClipboard('{group['c_total']}', 'btn_amount_{group_id}')">Copiar</button>
                        </td>
                    </tr>
''')

            # Add separator between groups (except after last group)
            if idx < len(groups) - 1:
                html_parts.append('                    <tr><td colspan="2" class="group-separator"></td></tr>\n')

        # Footer with total
        html_parts.append(f'''
                    <tr class="footer-row">
                        <td>TOTAL {year_label.upper()}</td>
                        <td class="amount">{self._format_decimal(total_c_total)}</td>
                    </tr>
                </tbody>
            </table>
        </div>
''')

        return ''.join(html_parts)

    def _html_footer(self) -> str:
        """Generate HTML footer"""
        return '''
    </div>
</body>
</html>
'''

    def _escape_js(self, text: str) -> str:
        """Escape text for use in JavaScript string"""
        return text.replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')


def export_grouped_to_html(
    document: LiquidationDocument,
    grouping_config: GroupingConfig,
    output_path: str,
    group_by_year: bool = True,
    group_by_concept: bool = True,
    group_by_custom: bool = False
) -> None:
    """
    Convenience function to export grouped concepts to HTML

    Args:
        document: LiquidationDocument with all records
        grouping_config: GroupingConfig with concept and custom group definitions
        output_path: Path where to save the HTML file
        group_by_year: Whether to group by year
        group_by_concept: Whether to group by concept
        group_by_custom: Whether to apply custom grouping
    """
    exporter = HTMLGroupedExporter(document, grouping_config)
    exporter.export_grouped_concepts(output_path, group_by_year, group_by_concept, group_by_custom)

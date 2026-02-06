"""
HTML Exporter for Datas Records (c_datas > 0)
Exports liquidation data filtered by c_datas > 0, showing per-record detail
with clave_recaudacion and clave_contabilidad compacted codes.
"""

from typing import List, Dict
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from ..models.liquidation import LiquidationDocument, TributeRecord
from ..models.grouping_config import GroupingConfig
from .html_grouped_exporter import HTMLGroupedExporter


class HTMLDatasExporter(HTMLGroupedExporter):
    """Exports records with c_datas > 0 to HTML format, inheriting shared logic."""

    def _filter_datas_records(self, records: List[TributeRecord]) -> List[TributeRecord]:
        """Filter records where c_datas > 0."""
        return [r for r in records if r.c_datas > Decimal('0')]

    def export_datas_report(
        self,
        output_path: str,
        group_by_year: bool = True,
        group_by_concept: bool = True,
        group_by_custom: bool = False
    ) -> int:
        """
        Export datas report to HTML.

        Returns:
            Number of records with c_datas > 0 (0 means nothing to export).
        """
        # Filter records with c_datas > 0
        datas_records = self._filter_datas_records(self.document.tribute_records)

        if not datas_records:
            return 0

        # Organize filtered data
        grouped_data = self._organize_datas_data(
            datas_records, group_by_year, group_by_concept, group_by_custom
        )

        # Generate HTML
        html_content = self._generate_datas_html(
            grouped_data, group_by_year, group_by_concept, group_by_custom
        )

        # Write to file
        Path(output_path).write_text(html_content, encoding='utf-8')
        return len(datas_records)

    def _organize_datas_data(
        self,
        records: List[TributeRecord],
        group_by_year: bool,
        group_by_concept: bool,
        group_by_custom: bool
    ) -> Dict:
        """Organize datas records according to grouping configuration."""
        if group_by_year:
            years_data = {}
            for year in sorted(set(r.ejercicio for r in records)):
                year_records = [r for r in records if r.ejercicio == year]
                years_data[year] = self._organize_datas_records(
                    year_records, group_by_concept, group_by_custom
                )
            return years_data
        else:
            return {None: self._organize_datas_records(
                records, group_by_concept, group_by_custom
            )}

    def _organize_datas_records(
        self,
        records: List[TributeRecord],
        group_by_concept: bool,
        group_by_custom: bool
    ) -> List[Dict]:
        """Organize datas records into groups, storing c_datas as amount."""
        if not group_by_concept and not group_by_custom:
            return [{
                'name': 'Todos los conceptos',
                'records': records,
                'c_datas': sum(r.c_datas for r in records)
            }]

        groups = []

        if group_by_concept and not group_by_custom:
            concept_groups = defaultdict(list)
            for record in records:
                concept_code = self.grouping_config.get_concept_code(record.clave_recaudacion)
                concept_name = self.grouping_config.concept_names.get(concept_code, concept_code)
                concept_groups[concept_name].append(record)

            for concept_name, concept_records in sorted(concept_groups.items()):
                groups.append({
                    'name': concept_name,
                    'records': concept_records,
                    'c_datas': sum(r.c_datas for r in concept_records)
                })

        elif group_by_custom:
            if group_by_concept:
                concept_groups = defaultdict(list)
                for record in records:
                    concept_code = self.grouping_config.get_concept_code(record.clave_recaudacion)
                    concept_groups[concept_code].append(record)

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
                            'c_datas': sum(r.c_datas for r in group_records)
                        })

                for concept_code, concept_records in sorted(concept_groups.items()):
                    if concept_code not in used_concepts:
                        concept_name = self.grouping_config.concept_names.get(concept_code, concept_code)
                        groups.append({
                            'name': concept_name,
                            'records': concept_records,
                            'c_datas': sum(r.c_datas for r in concept_records)
                        })
            else:
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
                            'c_datas': sum(r.c_datas for r in group_records)
                        })

                ungrouped = [r for r in records if id(r) not in used_records]
                if ungrouped:
                    groups.append({
                        'name': 'Sin agrupar',
                        'records': ungrouped,
                        'c_datas': sum(r.c_datas for r in ungrouped)
                    })

        return groups

    def _build_texto_sical_datas(self, ejercicio: int, group_name: str, records: List[TributeRecord]) -> str:
        """Build SICAL text for datas report.

        Format: CTA. OPAEF/{doc_year}, {group_name} ANULACION DERECHOS {claves_rec} {claves_cont}
        Note: doc_year is always the document's fiscal year (annual account).
        """
        claves_rec, claves_cont = self._collect_unique_claves(records)
        doc_year = self.document.ejercicio
        return (
            f"CTA. OPAEF/{doc_year}, {group_name} "
            f"ANULACION DERECHOS {claves_rec} {claves_cont}"
        )

    def _generate_datas_html(
        self,
        grouped_data: Dict,
        group_by_year: bool,
        group_by_concept: bool,
        group_by_custom: bool
    ) -> str:
        """Generate complete HTML document for datas report."""
        html_parts = [
            self._html_datas_header(),
            self._html_datas_document_info(),
        ]

        for year, groups in grouped_data.items():
            html_parts.append(self._html_datas_year_table(year, groups))

        html_parts.append(self._html_footer())
        return '\n'.join(html_parts)

    def _html_datas_header(self) -> str:
        """Generate HTML header with CSS and JavaScript for datas report."""
        return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Liquidación OPAEF - Informe Datas</title>
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
            background: linear-gradient(135deg, #8B4513 0%, #A0522D 100%);
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
            color: #8B4513;
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
            background-color: #FFF8F0;
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
            background: linear-gradient(135deg, #A0522D 0%, #8B4513 100%);
            color: white;
            text-align: left;
            padding: 15px 20px;
            font-size: 18px;
            font-weight: bold;
        }

        .year-table tbody tr {
            border-bottom: 1px solid #d0d0d0;
        }

        .year-table td, .year-table th {
            padding: 12px 15px;
            vertical-align: middle;
        }

        .label-cell {
            font-weight: bold;
            background-color: #F5E6D3;
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

        .detail-header {
            background-color: #F5E6D3;
            font-weight: bold;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #5D3A1A;
        }

        .detail-header th {
            padding: 8px 12px;
            border-bottom: 2px solid #D2B48C;
        }

        .detail-row td {
            padding: 6px 12px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            border-bottom: 1px solid #eee;
        }

        .detail-row:nth-child(even) {
            background-color: #FAFAF5;
        }

        .detail-row:nth-child(odd) {
            background-color: white;
        }

        .detail-amount {
            text-align: right;
            font-weight: bold;
            color: #8B4513;
        }

        .footer-row {
            background: linear-gradient(135deg, #F5E6D3 0%, #F0DCC8 100%);
            font-weight: bold;
            font-size: 16px;
        }

        .footer-row td {
            padding: 15px 20px;
        }

        .copy-btn {
            background-color: #8B4513;
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
            background-color: #6B3410;
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
            color: #8B4513;
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
                background: #8B4513 !important;
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
                background-color: #FFF8F0 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                padding: 15px;
                margin-bottom: 15px;
                border: 1px solid #ccc;
            }

            .print-year-header h2 {
                background: #8B4513 !important;
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
                background: #A0522D !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }

            .label-cell {
                background-color: #F5E6D3 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }

            .detail-header {
                background-color: #F5E6D3 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }

            .footer-row {
                background: #F5E6D3 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }

            .group-separator {
                background-color: #f5f5f5 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }

            @page {
                margin: 1.5cm;
                size: A4;
            }

            .year-table {
                margin-bottom: 10px;
            }

            .texto-sical {
                font-size: 11px;
            }

            .year-table td, .year-table th {
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

            .year-table td, .year-table th {
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

    def _html_datas_document_info(self) -> str:
        """Generate document information section for datas report."""
        datas_count = len(self._filter_datas_records(self.document.tribute_records))
        total_datas = sum(r.c_datas for r in self.document.tribute_records if r.c_datas > Decimal('0'))
        return f'''
        <div class="header">
            <h1>Liquidación OPAEF - Informe Datas</h1>
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
                <div class="doc-info-label">Registros con Datas</div>
                <div class="doc-info-value">{datas_count} registros</div>
            </div>
            <div class="doc-info-item">
                <div class="doc-info-label">Total Datas</div>
                <div class="doc-info-value">{self._format_decimal(total_datas)}</div>
            </div>
            <div class="doc-info-item">
                <div class="doc-info-label">Fecha Exportación</div>
                <div class="doc-info-value">{datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
            </div>
        </div>
'''

    def _html_datas_year_table(self, year: int, groups: List[Dict]) -> str:
        """Generate HTML table for a year's datas groups with per-record detail."""
        year_label = f"Ejercicio {year}" if year else "Todos los ejercicios"
        total_datas = sum(g['c_datas'] for g in groups)
        fecha_export_str = datetime.now().strftime('%d/%m/%Y %H:%M')

        html_parts = [f'''
        <div class="year-section">
            <div class="print-year-header">
                <h2>Liquidación OPAEF - Informe Datas</h2>
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
                        <th colspan="4" class="year-header">{year_label}</th>
                    </tr>
                </thead>
                <tbody>
''']

        for idx, group in enumerate(groups):
            group_id = f"datas_{year}_{idx}"
            ejercicio = year if year is not None else self.document.ejercicio
            texto_sical = self._build_texto_sical_datas(ejercicio, group['name'], group['records'])
            datas_formatted = self._format_decimal(group['c_datas'])
            partidas = self._get_partidas_from_records(group['records'])

            # Group info rows
            html_parts.append(f'''
                    <tr>
                        <td class="label-cell" colspan="1">Grupo</td>
                        <td class="value-cell" colspan="3"><strong>{group['name']}</strong></td>
                    </tr>
                    <tr>
                        <td class="label-cell" colspan="1">Texto SICAL</td>
                        <td class="value-cell" colspan="3">
                            <span class="texto-sical">{texto_sical}</span>
                            <button class="copy-btn" id="btn_sical_{group_id}" onclick="copyToClipboard('{self._escape_js(texto_sical)}', 'btn_sical_{group_id}')">Copiar</button>
                        </td>
                    </tr>
                    <tr>
                        <td class="label-cell" colspan="1">Aplicación</td>
                        <td class="value-cell" colspan="3">{partidas}</td>
                    </tr>
''')

            # Detail table header
            html_parts.append('''
                    <tr class="detail-header">
                        <th>Clave Recaudación</th>
                        <th>Clave Contabilidad</th>
                        <th>Concepto</th>
                        <th style="text-align: right;">Importe Datas</th>
                    </tr>
''')

            # Per-record detail rows
            for record in group['records']:
                rec_formatted = self._compact_codes([record.clave_recaudacion])
                cont_formatted = self._compact_codes([record.clave_contabilidad])
                html_parts.append(f'''
                    <tr class="detail-row">
                        <td>{rec_formatted}</td>
                        <td>{cont_formatted}</td>
                        <td>{record.concepto}</td>
                        <td class="detail-amount">{self._format_decimal(record.c_datas)}</td>
                    </tr>
''')

            # Group total
            html_parts.append(f'''
                    <tr>
                        <td class="label-cell" colspan="1">Total Datas</td>
                        <td class="value-cell" colspan="3">
                            <span class="amount">{datas_formatted}</span>
                            <button class="copy-btn" id="btn_amount_{group_id}" onclick="copyToClipboard('{group['c_datas']}', 'btn_amount_{group_id}')">Copiar</button>
                        </td>
                    </tr>
''')

            # Separator between groups
            if idx < len(groups) - 1:
                html_parts.append('                    <tr><td colspan="4" class="group-separator"></td></tr>\n')

        # Footer with year total
        html_parts.append(f'''
                    <tr class="footer-row">
                        <td colspan="3">TOTAL DATAS {year_label.upper()}</td>
                        <td class="amount">{self._format_decimal(total_datas)}</td>
                    </tr>
                </tbody>
            </table>
        </div>
''')

        return ''.join(html_parts)


def export_datas_to_html(
    document: LiquidationDocument,
    grouping_config: GroupingConfig,
    output_path: str,
    group_by_year: bool = True,
    group_by_concept: bool = True,
    group_by_custom: bool = False
) -> int:
    """
    Convenience function to export datas report to HTML.

    Returns:
        Number of records exported (0 means no records with c_datas > 0).
    """
    exporter = HTMLDatasExporter(document, grouping_config)
    return exporter.export_datas_report(
        output_path, group_by_year, group_by_concept, group_by_custom
    )

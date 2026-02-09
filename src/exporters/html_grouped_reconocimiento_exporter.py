"""
HTML Exporter for Grouped Records with OPAEF Year-of-Recognition splitting.
Same as the general grouped HTML report but splits OPAEF-managed concepts
where clave_recaudacion year differs from clave_contabilidad year.
"""

from typing import List, Dict
from decimal import Decimal
from collections import defaultdict

from ..models.liquidation import LiquidationDocument, TributeRecord
from ..models.grouping_config import GroupingConfig
from .html_grouped_exporter import HTMLGroupedExporter


class HTMLGroupedReconocimientoExporter(HTMLGroupedExporter):
    """Exports grouped records to HTML with OPAEF year-of-recognition splitting."""

    CONCEPTO_GESTION = {
        '102', '204', '205', '206', '208', '213', '218', '501', '700', '777'
    }

    @staticmethod
    def _extract_year_from_clave(clave: str) -> str:
        if not clave:
            return ''
        return clave.split('.')[0]

    def _is_opaef_concept(self, record: TributeRecord) -> bool:
        concept_code = self.grouping_config.get_concept_code(record.clave_recaudacion)
        return concept_code in self.CONCEPTO_GESTION

    def _has_mixed_years(self, record: TributeRecord) -> bool:
        rec_year = self._extract_year_from_clave(record.clave_recaudacion)
        cont_year = self._extract_year_from_clave(record.clave_contabilidad)
        return rec_year != cont_year

    def _get_reconocimiento_year(self, record: TributeRecord) -> int:
        if self._is_opaef_concept(record):
            cont_year = self._extract_year_from_clave(record.clave_contabilidad)
            if cont_year.isdigit():
                return int(cont_year)
        return record.ejercicio

    def _split_opaef_mixed_years(self, groups: List[Dict]) -> List[Dict]:
        """Split OPAEF records with mixed years into separate sub-groups."""
        result = []
        for group in groups:
            normal_records = []
            mixed_records = []

            for record in group['records']:
                if self._is_opaef_concept(record) and self._has_mixed_years(record):
                    mixed_records.append(record)
                else:
                    normal_records.append(record)

            if normal_records:
                result.append({
                    'name': group['name'],
                    'records': normal_records,
                    'c_total': sum(r.c_total for r in normal_records)
                })

            if mixed_records:
                mixed_by_cont_year = defaultdict(list)
                for r in mixed_records:
                    cont_year = self._extract_year_from_clave(r.clave_contabilidad)
                    mixed_by_cont_year[cont_year].append(r)

                for cont_year in sorted(mixed_by_cont_year.keys()):
                    year_records = mixed_by_cont_year[cont_year]
                    result.append({
                        'name': f"{group['name']} (Rec. {cont_year})",
                        'records': year_records,
                        'c_total': sum(r.c_total for r in year_records)
                    })

        return result

    def export_grouped_concepts(
        self,
        output_path: str,
        group_by_year: bool = True,
        group_by_concept: bool = True,
        group_by_custom: bool = False
    ) -> None:
        """Override to apply OPAEF year splitting and reconocimiento year grouping."""
        grouped_data = self._organize_reconocimiento_data(
            group_by_year, group_by_concept, group_by_custom
        )
        html_content = self._generate_html(
            grouped_data, group_by_year, group_by_concept, group_by_custom
        )

        from pathlib import Path
        Path(output_path).write_text(html_content, encoding='utf-8')

    def _organize_reconocimiento_data(
        self,
        group_by_year: bool,
        group_by_concept: bool,
        group_by_custom: bool
    ) -> Dict:
        """Organize data using reconocimiento year for OPAEF concepts."""
        if group_by_year:
            years_data_raw = defaultdict(list)
            for record in self.document.tribute_records:
                year = self._get_reconocimiento_year(record)
                years_data_raw[year].append(record)

            years_data = {}
            for year in sorted(years_data_raw.keys()):
                groups = self._organize_records(
                    years_data_raw[year], group_by_concept, group_by_custom
                )
                years_data[year] = self._split_opaef_mixed_years(groups)
            return years_data
        else:
            groups = self._organize_records(
                self.document.tribute_records, group_by_concept, group_by_custom
            )
            return {None: self._split_opaef_mixed_years(groups)}


def export_reconocimiento_to_html(
    document: LiquidationDocument,
    grouping_config: GroupingConfig,
    output_path: str,
    group_by_year: bool = True,
    group_by_concept: bool = True,
    group_by_custom: bool = False
) -> None:
    """Convenience function to export reconocimiento grouped report to HTML."""
    exporter = HTMLGroupedReconocimientoExporter(document, grouping_config)
    exporter.export_grouped_concepts(
        output_path, group_by_year, group_by_concept, group_by_custom
    )

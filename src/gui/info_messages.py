"""
Information messages for each tab in the application.

These messages explain to users what data is shown, how it's calculated/extracted,
and what validations are performed.
"""

COBROS_INFO = """INFORMACIÓN - Registros de Cobros

QUÉ SE MUESTRA:
• Todos los registros individuales de tributos extraídos del PDF
• Agrupados por año fiscal (ejercicio)
• Incluye: concepto, claves contables, importes voluntarios/ejecutivos,
  recargos, importes de diputación y líquido total

CÓMO SE EXTRAE:
• Datos extraídos directamente de las tablas del documento PDF
• Año fiscal: detectado automáticamente desde clave de recaudación
  (formato: 026/YYYY/...)
• Líquido: suma de todas las columnas de importes por registro

VALIDACIONES POR AÑO:
• Verde (✓): Los totales del año coinciden con "TOTAL EJERCICIO" del PDF
• Gris: Total "TOTAL EJERCICIO" extraído del PDF
• Rojo "CALCULADO": Muestra totales calculados cuando hay diferencias
• Tolerancia: ±0.01€

CÓDIGOS DE COLOR:
• Azul claro: Filas normales de datos
• Verde claro: Validación correcta para el año
• Gris: Total documentado del PDF
• Rojo claro: Diferencias encontradas (ver fila "CALCULADO")

COLUMNAS:
• Voluntaria: Recaudación en período voluntario
• Ejecutiva: Recaudación en vía ejecutiva
• Recargo: Recargos aplicados
• Dip. Vol./Ejec./Rec.: Importes correspondientes a Diputación
• Líquido: Total neto a favor del ayuntamiento"""


RESUMEN_INFO = """INFORMACIÓN - Resumen por Ejercicio

Esta tabla muestra tres filas de totales al final:

1. TOTAL (Calculado):
   • Se calcula sumando todos los registros individuales de tributos
     agrupados por año.
   • Representa lo que debería ser según los datos extraídos del PDF.
   • Color azul claro.

2. TOTAL (Documento):
   • Se extrae directamente de la tabla "TOTAL" del documento PDF.
   • Es el valor oficial que aparece en el documento original.
   • Color gris claro.

3. VALIDACIÓN:
   • ✓ Verde: Los valores calculados coinciden con el documento
     (tolerancia ±0.01€).
   • ⚠ Rojo: Hay diferencias entre calculado y documento.
     Muestra las diferencias por columna (+/- diferencia en euros).

Si la validación muestra diferencias, puede indicar:
   • Problemas en la extracción del PDF
   • Errores en el documento original
   • Registros individuales que no coinciden con el total declarado

Revise la configuración de extracción PDF en caso de diferencias."""


AGRUPACION_INFO = """INFORMACIÓN - Agrupación Personalizada

QUÉ SE MUESTRA:
• Registros agrupados según criterios personalizables
• Configuración por defecto agrupa por tipo de concepto
• Total general de todos los grupos

CÓMO SE CALCULA:
• Los registros se agrupan por códigos de concepto (último número
  de la clave de recaudación, ej: 026/2024/20/100/208 → código 208)
• Cada grupo suma los importes de todos los registros que coinciden
• Total: suma de todos los grupos configurados

CONFIGURACIÓN (Panel lateral):
• Puede editar las reglas de agrupación en tiempo real
• Añadir/eliminar grupos personalizados por código de concepto
• Definir qué códigos pertenecen a cada grupo personalizado
• Agrupar por año o consolidar todos los años

NOTA IMPORTANTE:
• Los conceptos se agrupan por CÓDIGO, no por nombre
• IBI RÚSTICA (205) e IBI URBANA (208) son conceptos separados
• MULTAS TRÁFICO (777) e IVTM (501) son conceptos separados
• Cada concepto se muestra individualmente salvo que lo agrupe manualmente

EJEMPLOS DE AGRUPACIÓN (según configuración actual):
• Grupo "SUMINISTRO_AGUA": agrupa códigos 450 (Suministro de agua),
  452 (Canon) y 750 (Cuota fija agua)
• Grupo "IVA_RECIBOS_AGUA": agrupa códigos 451 (IVA), 573 (IVA cuota fija),
  665 (IVA s/canon), 752 (IVA s/agua) y 753 (IVA s/conservación)
• Grupo "ENTRADA VEHICULOS": agrupa códigos 025 (Entrada vehículos)
  y 329 (Reserva aparcamiento)
• Grupo "TASAS-OCUP-VIA-P": agrupa códigos 006 (Tasas municipales),
  062 (Ocupac. vía pública), 663 (Escombros) y 675 (Cubas)

EXPORTACIÓN:
• Los datos agrupados pueden exportarse a Excel o HTML
• Mantiene la estructura de grupos configurada
• Incluye totales por grupo y total general

USO RECOMENDADO:
• Para análisis consolidados por tipo de tributo
• Para informes resumidos a presentar
• Para identificar principales fuentes de recaudación"""


DEDUCCIONES_INFO = """INFORMACIÓN - Deducciones

QUÉ SE MUESTRA:
• Desglose de todas las deducciones aplicadas al líquido
• Organizadas en 4 categorías principales
• Total de deducciones

CÓMO SE EXTRAE:
• Datos extraídos de la tabla "DEDUCCIONES" del PDF
• Ubicación: generalmente en página 2 o última página del documento
• Total: suma automática de todos los conceptos de deducción

CATEGORÍAS:

1. RECAUDACIÓN:
   • Tasa Voluntaria: Comisión por gestión de cobros voluntarios
   • Tasa Ejecutiva: Comisión por gestión de cobros ejecutivos
   • Tasa Ejecutiva Sin Recargo: Gestión ejecutiva sin recargo aplicado
   • Tasa Baja Órgano Gestor: Bajas tramitadas por órgano gestor

2. TRIBUTARIA:
   • Tasa Gestión Tributaria: Servicios de gestión tributaria
   • Tasa Gestión Censal: Mantenimiento de censos tributarios
   • Tasa Gestión Catastral: Servicios catastrales

3. MULTAS/SANCIONES:
   • Tasa Sanción Tributaria: Sanciones por infracciones tributarias
   • Tasa Sanción Recaudación: Sanciones en gestión recaudatoria
   • Tasa Sanción Inspección: Sanciones por inspección
   • Tasa Multas de Tráfico: Gestión de multas de tráfico

4. OTRAS DEDUCCIONES:
   • Gastos Repercutidos: Gastos varios repercutidos
   • Anticipos: Anticipos realizados durante el ejercicio
   • Intereses por Anticipo: Intereses generados por anticipos
   • Expedientes Compensación: Compensaciones procesadas
   • Expedientes Ingresos Indebidos: Devoluciones por ingresos indebidos

VALIDACIÓN:
• El total de deducciones se usa para calcular "A LIQUIDAR"
• Fórmula: TOTAL LÍQUIDO - TOTAL DEDUCCIONES = A LIQUIDAR
• Verifique que esta fórmula se cumpla en el documento"""


DEVOLUCIONES_INFO = """INFORMACIÓN - Devoluciones

QUÉ SE MUESTRA:
• Expedientes de devolución procesados durante el ejercicio
• Resumen agregado por concepto de tributo
• Total de devoluciones

CÓMO SE EXTRAE:
• Datos extraídos de la tabla de devoluciones del PDF
• Ubicación: generalmente en página 3 o última página del documento
• Incluye detalle por expediente y resumen por concepto

EXPEDIENTES INDIVIDUALES:
• Nº Expte: Número del expediente de devolución
• Nº Resolución: Número de resolución administrativa
• Nº Solic: Número de solicitud
• Total Devolución: Importe total a devolver
• Entidad: Parte correspondiente al ayuntamiento
• Diputación: Parte correspondiente a la diputación
• Intereses: Intereses calculados sobre la devolución
• Comp. Trib.: Compensación tributaria aplicada
• A Deducir: Cantidad final a deducir del líquido

RESUMEN POR CONCEPTO:
• Agrupa las devoluciones por tipo de tributo
• Muestra totales por: IBI Urbana, IBI Rústica, IVTM, etc.

IMPACTO EN LIQUIDACIÓN:
• Las devoluciones se descuentan del importe líquido
• El campo "A Deducir" indica la cantidad que afecta al resultado final
• Verifique que coincida con los importes documentados

CASOS ESPECIALES:
• Devoluciones con intereses: aumentan el importe total
• Compensaciones tributarias: pueden reducir el importe a devolver
• Devoluciones parciales: solo afectan a la parte de entidad o diputación"""

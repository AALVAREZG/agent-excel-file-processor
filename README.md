# Liquidación OPAEF - Extractor de Datos

Aplicación de escritorio para procesar datos de recaudación anual de la Diputación Provincial.

## Características

- **Carga de archivos Excel con datos de recaudación anual** ⭐ NUEVO
- Extracción precisa de registros de cobros por tributo
- Procesamiento de múltiples ejercicios fiscales en un solo archivo
- **Exportación a Excel con formato profesional**
- **Exportación HTML agrupada por conceptos**
  - Agrupación flexible por año, concepto y grupos personalizados
  - Formato profesional con funcionalidad de impresión
  - Mapeo automático a partidas contables locales
  - Compactación inteligente de códigos
- Validación automática de totales (documento y por año)
- Interfaz moderna y fácil de usar
- Soporte para archivos Excel (.xlsx, .xls) y PDF (legacy)
- Portable - no requiere instalación

## Tipos de Datos Extraídos

### 1. Registros de Cobros
**Formato Excel (Cuenta Recaudatoria Anual):**
- Columnas: ENT, C_EJERCICIO, C_CONCEPTO, CLAVE_C, CLAVE_R, C_VOLUNTARIA, C_EJECUTIVA, C_PENDIENTE
- Múltiples ejercicios fiscales en un solo archivo
- IBI Rústica y Urbana
- Impuesto sobre Vehículos de Tracción Mecánica (IVTM)
- Multas de Tráfico/Circulación
- Importes: Voluntaria, Ejecutiva
- Claves de Contabilidad y Recaudación

### 2. Resumen por Ejercicio
- Totales agrupados por año fiscal (2008-2025)
- Cálculos de líquido
- Validación de sumas
- Contador de registros por año


## Instalación

### Requisitos
- Python 3.8 o superior
- Windows 10/11 (puede adaptarse a Linux/Mac)

### Instalación de Dependencias

```bash
pip install -r requirements.txt
```

## Uso

### Ejecutar la Aplicación

```bash
# Activar entorno virtual y ejecutar
venv\Scripts\python main.py
```

### Flujo de Trabajo

1. **Cargar Excel**: Haz clic en "Cargar Excel" y selecciona tu archivo de cuenta recaudatoria anual (.xlsx)
2. **Revisar Datos**: Navega por las pestañas para ver los datos extraídos:
   - **Registros de Cobros**: Tabla completa con todos los registros
   - **Resumen por Ejercicio**: Totales agrupados por año fiscal
   - **Agrupación Personalizada**: Vista agrupada por conceptos

### Ejemplo con archivo de prueba

```bash
# Ejecutar test de extracción
venv\Scripts\python test_excel_extraction.py
```

Esto cargará `data/CTA_2025_026.xlsx` y mostrará:
- 615 registros extraídos
- 14 ejercicios fiscales (2008-2025)
- Totales validados correctamente
 
### Exportación a Excel

El archivo Excel generado contiene múltiples hojas:
- **Información**: Datos del documento
- **Registros de Cobros**: Tabla completa de tributos con todas las columnas
- **Resumen por Ejercicio**: Totales agrupados por año fiscal

### Exportación HTML Agrupada ⭐ NUEVO

La aplicación genera reportes HTML profesionales con agrupación flexible de conceptos, ideal para adjuntar a documentos contables por año fiscal.

#### Características Principales

**1. Agrupación Flexible**
- **Por año fiscal**: Separa los cobros por ejercicio (ej. 2023, 2024, 2025)
- **Por concepto**: Agrupa automáticamente por tipo de tributo:
  - IBI Urbana, IBI Rústica, IBI Especial
  - IVTM (Impuesto sobre Vehículos)
  - Multas de Tráfico
  - Intereses de Demora
  - Y más...
- **Grupos personalizados**: Permite crear agrupaciones customizadas combinando múltiples conceptos

**2. Mapeo a Partidas Contables**

El sistema incluye un mapeo automático de códigos Órgano a partidas contables locales:

| Concepto OPAEF | Partida Local | Descripción |
|----------------|---------------|-------------|
| 208 | 113 | IBI Urbana |
| 205 | 112 | IBI Rústica |
| 501 | 115 | IVTM |
| 777 | 39120 | Multas Tráfico |
| 700 | 393 | Intereses de Demora |
| 573, 665, 752, 753 | 10049 | IVA Agua |
| 450, 678, 750, 752 | 300 | Suministro Agua |

*El mapeo completo incluye 44 conceptos diferentes*

**3. Compactación Inteligente de Códigos**

Los códigos de recaudación y contabilidad se compactan automáticamente para facilitar la lectura:

```
ANTES:
026/2021/58/064/573 026/2021/58/064/665 026/2021/58/068/573 026/2021/58/068/665
2023/E/0000783 2023/E/0000784 2023/E/0001274 2023/E/0001275

DESPUÉS:
026/2021/58/{064,068}/573,665
2023/E/783,784,1274,1275
```

**4. Formato de Texto SICAL Mejorado**

Cada grupo incluye un texto SICAL formateado que identifica claramente:
```
OPAEF. REGULARIZACION COBROS {año} - {nombre_grupo} LIQ. {num_liquidacion} MTO. PAGO {num_mandamiento} {códigos_compactados}
```

Ejemplo:
```
OPAEF. REGULARIZACION COBROS 2024 - IBI_URBANA LIQ. 00000623 MTO. PAGO 2025/0016 026/2024/58/{064,068,086}/208 2024/E/783,784,786
```

**5. Funcionalidad de Impresión Profesional**

El HTML incluye un botón "🖨️ Imprimir" que genera reportes optimizados para impresión:

- **Cada año en página separada**: Ideal para adjuntar a documentos contables por ejercicio
- **Encabezado automático por página**: Incluye información del documento en cada hoja
  - Entidad y código
  - Número de liquidación
  - Mandamiento de pago y fecha
  - Ejercicio fiscal específico
  - Fecha de exportación
- **Preservación de colores**: Mantiene fondos y formato para mejor presentación
- **Optimización para A4**: Márgenes y fuentes ajustados para papel estándar

#### Ejemplo de Uso

1. Cargar y procesar el PDF
2. En la pestaña "Agrupación", configurar:
   - ☑ Agrupar por año
   - ☑ Agrupar por concepto
   - ☐ Aplicar grupos personalizados (opcional)
3. Hacer clic en "Exportar HTML Agrupado"
4. Abrir el archivo HTML generado en el navegador
5. Usar el botón "🖨️ Imprimir" para generar PDFs por año

#### Estructura del HTML Generado

```html
📄 liquidacion_XXXXXXXX_agrupado.html
├── Encabezado (solo en pantalla)
│   ├── Título
│   ├── Botón de Impresión
│   └── Información del Documento
└── Secciones por Año (cada una en página separada al imprimir)
    ├── Encabezado de Página (solo en impresión)
    │   ├── Título "Liquidación OPAEF"
    │   └── Datos del Documento (incluyendo año específico)
    └── Tabla del Año
        ├── Cabecera "Ejercicio XXXX"
        ├── Grupos de Conceptos
        │   ├── Nombre del Grupo
        │   ├── Texto SICAL (con botón copiar)
        │   ├── Aplicación (partidas contables)
        │   └── Importe Líquido (con botón copiar)
        └── Total del Año
```

#### Ventajas del Formato HTML

- **Interactivo**: Botones para copiar textos e importes al portapapeles
- **Portable**: Un solo archivo independiente, sin dependencias externas
- **Profesional**: Diseño responsive con degradados y tipografía moderna
- **Funcional**: Optimizado tanto para visualización en pantalla como para impresión
- **Trazable**: Incluye fecha y hora de exportación automática

## Estructura del Proyecto

```
liquidacion-opaef/
├── main.py                 # Punto de entrada
├── requirements.txt        # Dependencias
├── src/
│   ├── gui/               # Interfaz gráfica
│   │   └── main_window.py
│   ├── extractors/        # Extracción de PDF
│   │   └── pdf_extractor.py
│   ├── models/            # Modelos de datos
│   │   ├── liquidation.py
│   │   └── grouping_config.py
│   ├── exporters/         # Exportación
│   │   ├── excel_exporter.py
│   │   └── html_grouped_exporter.py  ⭐ NUEVO
│   ├── validators/        # Validaciones (futuro)
│   └── utils/             # Utilidades
│       └── config_manager.py
├── scripts/               # Herramientas de desarrollo
│   ├── debug_pdf_tables.py
│   └── debug_pdf_tables_gui.py
├── config/                # Configuraciones
└── tests/                 # Tests unitarios
```

## Creación de Ejecutable Portable

Para crear un archivo .exe portable:

```bash
pyinstaller --onefile --windowed --name="LiquidacionOPAEF" main.py
```

El ejecutable se generará en la carpeta `dist/`.

## Validaciones Implementadas

La aplicación implementa un sistema de validación para garantizar la integridad de los datos extraídos:

### Validación Global (Nivel Documento)

- **Verificación de sumas totales**: Compara la suma de TODOS los registros de cobros contra los totales calculados
- **Validación por ejercicio**: Verifica que los totales por año coincidan con la suma de registros de ese año
- **Tolerancia de redondeo**: Permite diferencias menores a 0.01€ por redondeos

### Formato de Números

La aplicación maneja correctamente:
- Formato europeo: 1.234,56
- Separadores de miles
- Decimales con coma o punto

## Licencia

Uso interno - Todos los derechos reservados

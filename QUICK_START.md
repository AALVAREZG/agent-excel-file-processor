# Quick Start Guide

## 🚀 Launch Application

```bash
cd C:\Users\anton\desarrollo\claude-code\AYTO-OTROS\opaef-cta-excel
venv\Scripts\python main.py
```

## 📥 Load Excel File

1. Click **"Cargar Excel"** button in the GUI
2. Navigate to `data\CTA_2025_026.xlsx` (or your file)
3. Wait for extraction (should take 1-2 seconds)
4. Data appears in tabs automatically

## 📊 View Data

Three tabs available:

- **Registros de Cobros** - All 615 records in table format
- **Resumen por Ejercicio** - 14 years summarized (2008-2025)
- **Agrupación Personalizada** - Group by concepts (configurable)

## 💾 Export Data

### Excel Export
Click **"Exportar a Excel"** → Save location → Done
- Creates multi-sheet workbook
- Professional formatting
- All data included

### HTML Export
Click **"Exportar HTML Agrupado"** → Save location → Done
- Grouped by year and concept
- Print-optimized
- SICAL text formatting included

## 🔧 Test Extraction (Optional)

```bash
venv\Scripts\python test_excel_extraction.py
```

Expected output:
```
[OK] Extraction successful!
- 615 records loaded
- 14 fiscal years
- Totals validated: 162,279,805.00€
```

## ⚙️ Configuration

Click **"Configuración"** button to:
- Set concept grouping rules
- Adjust appearance (fonts, colors)
- Configure custom concept groups

## 📁 File Format

Your Excel file must have these columns:
```
ENT | C_EJERCICIO | C_CONCEPTO | CLAVE_C | CLAVE_R |
C_CARGO | C_DATAS | C_VOLUNTARIA | C_EJECUTIVA | C_PENDIENTE
```

## 🆘 Troubleshooting

**Application won't start?**
```bash
# Reinstall dependencies
venv\Scripts\pip install -r requirements.txt
```

**Excel file won't load?**
- Check all required columns exist
- Verify data types (years as numbers, not text)
- Run test script to see detailed error

**Need to create virtual environment again?**
```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

## 📞 Quick Commands

| Action | Command |
|--------|---------|
| Run GUI | `venv\Scripts\python main.py` |
| Test extraction | `venv\Scripts\python test_excel_extraction.py` |
| Reinstall deps | `venv\Scripts\pip install -r requirements.txt` |
| Check Python version | `python --version` |

---

**Sample File Location:** `data\CTA_2025_026.xlsx`
**Documentation:** See `MIGRATION_GUIDE.md` and `README.md`

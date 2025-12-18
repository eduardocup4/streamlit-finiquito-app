# Finiquito Application - Deployment & Testing Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize System
```bash
# Generate Excel templates
python scripts/generate_templates.py

# Generate test data
python scripts/generate_test_data.py
```

### 3. Run Application
```bash
# Linux/Mac
./run.sh

# Windows
run.bat

# Or directly with Streamlit
streamlit run main.py
```

## ✅ System Components Status

### Core Modules (COMPLETE)
- ✅ **Domain Layer**
  - `entities.py` - Data models for Employee, PayrollMonth, etc.
  - `calculator.py` - Finiquito calculation engine
  - `validators.py` - Data validation rules

- ✅ **Infrastructure Layer**  
  - `database/models.py` - SQLAlchemy ORM models
  - `database/connection.py` - Database connection management
  - `excel/excel_adapter.py` - Document generation (6 types)
  - `excel/excel_reader.py` - Excel file reading
  - `qr/qr_generator.py` - QR code stamping

- ✅ **Application Layer**
  - `auth/auth_handler.py` - Authentication & authorization
  - `main.py` - Application entry point with navigation

### Pages (COMPLETE)
1. ✅ **Upload Page** - File upload interface
2. ✅ **Mapping Page** - Column mapping configuration  
3. ✅ **Case Selection** - Employee & parameters selection
4. ✅ **Preview Page** - Calculation preview & execution
5. ✅ **Generate Page** - Document generation with QR stamps
6. ✅ **Case History** - Search, filter, statistics
7. ✅ **Case Detail** - Full case view with editing
8. ✅ **Admin Page** - System configuration (7 tabs)

### Document Templates (COMPLETE)
- ✅ F_Finiquito - Main severance document
- ✅ Memo_Finalización - Termination memorandum
- ✅ F_Salida - Exit form with checklist
- ✅ F_Equipos - Equipment return form
- ✅ Contable_Preview - Accounting view
- ✅ Rechazo_Post - Post-exam rejection

### Test Data (COMPLETE)
- ✅ 3 months of payroll data (5 employees)
- ✅ RDP personal database
- ✅ Company name variations for homologation testing

## 🧪 Testing the Application

### Step 1: Login
Use one of the default accounts:
- **Admin**: admin / admin123
- **Operator**: operator / oper123  
- **Viewer**: viewer / view123

### Step 2: Test Workflow

#### Upload Files
1. Navigate to "📤 Cargar Archivos"
2. Upload test files from `/test_data/`:
   - `planilla_*_mes1.xlsx` (Mes 1)
   - `planilla_*_mes2.xlsx` (Mes 2)
   - `planilla_*_mes3.xlsx` (Mes 3)
   - `rdp_personal.xlsx` (RDP)
3. Select "Planilla" sheet for payroll files
4. Select "RDP" sheet for RDP file

#### Map Columns
1. Navigate to "🔗 Mapeo de Columnas"
2. Map required fields:
   - Empresa → "Empresa"
   - CI → "Nro. Doc"
   - Nombre → "Nombre"
   - Unidad → "Unidad de Negocio"
   - Cargo → "Ocup. que Desempeña"
   - Fecha Ingreso → "FechaIngreso"
   - Haber Básico → "HaberBasico"
   - Bono Antigüedad → "BonoAntiguedad"
   - Total Ganado → "TotalGanado"
3. Optional: Map "Otros Bonos" → "Otros Bonos"

#### Select Case
1. Navigate to "👤 Selección de Caso"
2. Select an employee from dropdown
3. Enter case parameters:
   - Pay Until Date (last day worked)
   - Request Date
   - Motivo de Retiro (reason for termination)

#### Preview & Calculate
1. Navigate to "📋 Vista Previa y Cálculo"
2. Review employee data from all 3 months
3. Add manual inputs if needed:
   - Bono Refrigerio
   - Comisiones
   - Other concepts
4. Click "Calcular Finiquito"
5. Review calculation results

#### Generate Documents
1. Navigate to "📄 Generar Documentos"
2. Select documents to generate:
   - F_Finiquito (always without stamp)
   - Memo_Finalización (optional CITE)
   - F_Salida, F_Equipos, etc.
3. Toggle QR stamps per document
4. Click "Generar Documentos"
5. Download generated files

### Step 3: Test Management Features

#### Case History
1. Navigate to "📚 Historial de Casos"
2. Use search and filters:
   - Search by CI or name
   - Filter by status
   - Filter by date range
3. View statistics dashboard
4. Click on case to view details

#### Case Detail
1. From History, click on a case
2. Browse tabs:
   - Resumen - Overview
   - Cálculo Detallado - Full calculation
   - Documentos - Generated files
   - Editar Metadata - Update status
   - Historial - Audit log

#### Admin Panel (Admin only)
1. Navigate to "⚙️ Administración"
2. Test each tab:
   - **Homologación**: Add company aliases
   - **Motivos**: Configure termination reasons
   - **Plantillas**: Upload custom templates
   - **Usuarios**: View users
   - **Configuración**: System settings
   - **Dashboard**: System metrics
   - **Base de Datos**: Database management

## 📁 File Structure

```
test_data/
├── planilla_2025_09_mes1.xlsx
├── planilla_2025_10_mes2.xlsx  
├── planilla_2025_11_mes3.xlsx
├── rdp_personal.xlsx
└── test_data_info.txt

storage/
├── templates/
│   ├── f_finiquito_template.xlsx
│   ├── memo_finalizacion_template.xlsx
│   ├── f_salida_template.xlsx
│   ├── f_equipos_template.xlsx
│   ├── contable_preview_template.xlsx
│   └── rechazo_post_template.xlsx
├── uploads/  (uploaded files stored here)
└── outputs/  (generated documents stored here)
```

## 🐛 Troubleshooting

### Database Issues
```bash
# Reset database
rm finiquito.db
python scripts/init_database.py
```

### Missing Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Clear Streamlit Cache
```bash
./run.sh --clear-cache
```

### Port Already in Use
```bash
# Kill existing Streamlit process
pkill -f streamlit
# Or use different port
streamlit run main.py --server.port=8502
```

## 📊 Test Employees

The test data includes 5 employees:
1. Juan Carlos Mendoza López (CI: 4567890)
2. María Elena Vargas Castro (CI: 5678901)
3. Roberto Fernández Quiroga (CI: 6789012)
4. Ana Patricia Rojas Salinas (CI: 7890123)
5. Carlos Alberto Gutiérrez (CI: 8901234)

Each has:
- 3 months of payroll history
- Personal data in RDP
- Varying salaries and bonuses
- Different company name variations

## 🎯 Key Features to Test

1. **Homologation**: Test with "Alianza Seguros SA" vs "ALIANZA SEGUROS S.A."
2. **Validation**: Try uploading incomplete data to see errors
3. **Manual Inputs**: Add custom bonuses and deductions
4. **QR Stamps**: Generate documents with/without stamps
5. **Audit Trail**: Check audit logs after operations
6. **Role Permissions**: Test different user roles
7. **Search/Filter**: Use various filter combinations in History
8. **Document Download**: Verify all generated files are downloadable

## 📝 Known Limitations

1. Email notifications not implemented (planned feature)
2. PDF export not implemented (Excel only)
3. Batch processing not available (single case at a time)
4. No data import/export functionality yet
5. Basic authentication (no password recovery)

## 🚦 System Status

| Component | Status | Notes |
|-----------|--------|-------|
| Core Calculation Engine | ✅ Ready | Fully tested |
| Document Generation | ✅ Ready | 6 document types |
| Database Layer | ✅ Ready | SQLite/PostgreSQL |
| Authentication | ✅ Ready | 3 roles |
| QR Stamping | ✅ Ready | Per-document control |
| Admin Panel | ✅ Ready | 7 management sections |
| Audit Logging | ✅ Ready | All operations logged |
| Test Data | ✅ Ready | 5 employees, 3 months |

## 🎉 Ready for Testing!

The application is fully functional and ready for comprehensive testing. All 8 pages are operational, document generation works with QR stamps, and the admin panel provides complete system configuration.

---
*Last Updated: December 2025*

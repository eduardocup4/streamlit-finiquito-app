# 🔍 GUÍA DE VALIDACIÓN LOCAL - Sistema de Finiquitos

## ✅ ESTADO DE LA APLICACIÓN

### Estructura Validada
- ✅ **23 archivos Python** compilados sin errores
- ✅ **6 plantillas Excel** presentes y válidas
- ✅ **4 archivos de datos de prueba** listos
- ✅ **8 páginas de Streamlit** funcionales
- ✅ **Base de datos SQLite** con esquema completo

---

## 📦 INSTALACIÓN EN LOCAL

### 1. Requisitos Previos
```bash
# Python 3.8 o superior
python --version

# pip actualizado
pip --version
```

### 2. Instalar Dependencias

#### Opción A: Instalación Completa (Recomendada)
```bash
cd finiquito_app
pip install -r requirements.txt
```

#### Opción B: Instalación Mínima (Más Rápida)
```bash
pip install streamlit pandas openpyxl pydantic pydantic-settings qrcode Pillow sqlalchemy python-dateutil
```

### 3. Verificar Instalación
```bash
# Ejecutar script de validación
python validate_setup.py
```

---

## 🚀 EJECUTAR LA APLICACIÓN

### Opción 1: Comando Directo
```bash
streamlit run main.py
```

### Opción 2: Script de Inicio (Linux/Mac)
```bash
chmod +x run.sh
./run.sh
```

### Opción 3: Script de Inicio (Windows)
```cmd
run.bat
```

**La aplicación se abrirá en:** `http://localhost:8501`

---

## 🔐 CREDENCIALES DE ACCESO

### Usuarios de Prueba

| Usuario | Contraseña | Rol | Permisos |
|---------|-----------|-----|----------|
| `admin` | `admin123` | Admin | Todos los permisos |
| `operator` | `oper123` | Operador | Crear y generar documentos |
| `viewer` | `view123` | Visor | Solo visualización |

---

## 🧪 FLUJO DE PRUEBA COMPLETO

### Paso 1: Login
1. Abrir `http://localhost:8501`
2. Ingresar con `admin` / `admin123`
3. Verificar que aparezca el panel principal

### Paso 2: Cargar Archivos
1. Ir a "📤 Cargar Archivos"
2. Cargar los 4 archivos desde `test_data/`:
   - `planilla_2025_09_mes1.xlsx` (Mes 1 - más antiguo)
   - `planilla_2025_10_mes2.xlsx` (Mes 2)
   - `planilla_2025_11_mes3.xlsx` (Mes 3 - más reciente)
   - `rdp_personal.xlsx` (Base de datos personal)
3. Click en "Procesar archivos"

### Paso 3: Mapeo de Columnas
1. Ir a "🔗 Mapeo de Columnas"
2. Seleccionar hojas (generalmente la primera hoja de cada archivo)
3. Verificar mapeo automático de campos
4. Guardar configuración

### Paso 4: Selección de Caso
1. Ir a "👤 Selección de Caso"
2. Buscar empleado por CI o nombre
3. Ejemplo: Buscar "María García" o CI "7890123"
4. Seleccionar empleado

### Paso 5: Configurar Parámetros
1. Ingresar fecha de pago hasta
2. Seleccionar motivo de retiro (ej: "RENUNCIA")
3. Ajustar parámetros si es necesario
4. Click en "Continuar a Vista Previa"

### Paso 6: Vista Previa y Cálculo
1. Ir a "📋 Vista Previa y Cálculo"
2. Revisar información del empleado
3. Click en "Calcular Finiquito"
4. Verificar resultados:
   - Promedio de 3 meses
   - Antigüedad calculada
   - Beneficios (aguinaldo, vacaciones, etc.)
   - Total a pagar

### Paso 7: Generar Documentos
1. Ir a "📄 Generar Documentos"
2. Seleccionar documentos a generar:
   - ✅ F-Finiquito (Principal)
   - ✅ Memorándum de Finalización
   - ✅ Formulario de Salida
   - ✅ Formulario de Equipos
   - ✅ Vista Previa Contable
   - ⬜ Rechazo Post-Examen (opcional)
3. Habilitar QR Stamp (opcional)
4. Click en "Generar Documentos Seleccionados"
5. Descargar archivos desde `storage/outputs/`

### Paso 8: Historial
1. Ir a "📚 Historial de Casos"
2. Verificar que el caso aparezca en la lista
3. Click en "Ver Detalle"
4. Revisar toda la información almacenada

### Paso 9: Panel de Administración
1. Ir a "⚙️ Administración"
2. Revisar:
   - Usuarios registrados
   - Configuración del sistema
   - Estadísticas de uso
   - Motivos de retiro configurados

---

## 📊 DATOS DE PRUEBA INCLUIDOS

### Empleados de Ejemplo (en test_data/)

| Nombre | CI | Empresa | Fecha Ingreso |
|--------|----| --------|---------------|
| Juan Pérez | 1234567 | Empresa A | 01/01/2020 |
| María García | 7890123 | Empresa B | 15/03/2021 |
| Carlos López | 4567890 | Empresa A | 10/06/2019 |
| Ana Martínez | 2345678 | Empresa C | 01/09/2022 |
| Pedro Rodríguez | 5678901 | Empresa B | 20/11/2020 |

### Campos en Planillas
- Nombre completo
- CI
- Empresa
- Unidad/Departamento
- Ocupación/Cargo
- Fecha de ingreso
- Fecha de nacimiento
- Haber básico
- Bono de antigüedad
- Total ganado
- Otros bonos

---

## 🔧 VALIDACIONES A REALIZAR

### Nivel 1: Funcionalidad Básica
- [ ] La app inicia sin errores
- [ ] Login funciona correctamente
- [ ] Se pueden cargar archivos Excel
- [ ] El mapeo detecta columnas automáticamente
- [ ] Se pueden buscar empleados
- [ ] El cálculo produce resultados

### Nivel 2: Cálculos
- [ ] Antigüedad se calcula correctamente (años, meses, días)
- [ ] Promedio de 3 meses es correcto
- [ ] Aguinaldo proporcional es correcto (1/12 por mes)
- [ ] Vacaciones se calculan según antigüedad
- [ ] Indemnización se aplica según motivo de retiro
- [ ] Desahucio se aplica correctamente
- [ ] Quinquenios se calculan (si aplica)

### Nivel 3: Documentos
- [ ] Se generan todos los documentos seleccionados
- [ ] Los documentos contienen la información correcta
- [ ] El QR stamp se añade correctamente
- [ ] Los archivos se guardan en `storage/outputs/`
- [ ] Los nombres de archivo son únicos

### Nivel 4: Base de Datos
- [ ] Los casos se guardan correctamente
- [ ] El historial muestra todos los casos
- [ ] Los detalles del caso son completos
- [ ] Las auditorías se registran
- [ ] Los documentos generados se vinculan al caso

### Nivel 5: Seguridad y Roles
- [ ] El rol "viewer" solo puede ver
- [ ] El rol "operator" puede generar documentos
- [ ] El rol "admin" accede a todo
- [ ] No se pueden acceder páginas sin permisos

---

## ⚠️ PROBLEMAS COMUNES Y SOLUCIONES

### Problema 1: Error al importar módulos
```
ModuleNotFoundError: No module named 'streamlit'
```
**Solución:**
```bash
pip install -r requirements.txt
```

### Problema 2: Base de datos bloqueada
```
database is locked
```
**Solución:**
```bash
rm finiquito_app.db
# La app creará una nueva base de datos al iniciar
```

### Problema 3: Puerto 8501 en uso
```
Address already in use
```
**Solución:**
```bash
# Cambiar puerto
streamlit run main.py --server.port 8502
```

### Problema 4: Archivos Excel no se leen
```
FileNotFoundError o pandas error
```
**Solución:**
```bash
pip install --upgrade openpyxl xlrd
```

### Problema 5: Error con pydantic
```
ImportError: cannot import name 'BaseSettings'
```
**Solución:**
```bash
pip install pydantic pydantic-settings --upgrade
```

---

## 📝 CHECKLIST DE VALIDACIÓN RÁPIDA

Ejecuta este checklist para validar que todo funciona:

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Verificar instalación
python validate_setup.py

# 3. Iniciar aplicación
streamlit run main.py

# 4. En el navegador:
# - Login con admin/admin123
# - Cargar archivos de test_data/
# - Seleccionar empleado "María García"
# - Calcular finiquito con motivo "RENUNCIA"
# - Generar todos los documentos
# - Verificar en storage/outputs/

# 5. Verificar resultados esperados:
# - Antigüedad: Depende de la fecha de ingreso vs fecha de cálculo
# - Promedio 3 meses: Suma de los 3 totales / 3
# - Aguinaldo: (Promedio / 12) * meses trabajados en el año
# - Vacaciones: Días según antigüedad * (Promedio / 30)
```

---

## 🎯 VERIFICACIÓN EXITOSA

Si completaste todos los pasos sin errores, la aplicación está **100% funcional** en tu entorno local.

### Siguiente Paso: Producción
Para desplegar en producción:
1. Cambiar contraseñas por defecto
2. Configurar base de datos PostgreSQL (opcional)
3. Configurar variables de entorno (.env)
4. Habilitar HTTPS
5. Configurar backup automático

---

## 📞 SOPORTE

Si encuentras algún problema:
1. Revisa el archivo `DEPLOYMENT_GUIDE.md`
2. Verifica los logs en la terminal de Streamlit
3. Ejecuta `python validate_setup.py` para diagnóstico

**Desarrollado por JELB** | Versión 1.0.0

# Sistema de Cálculo de Finiquitos - Bolivia

Sistema integral para el cálculo y generación automatizada de documentos de liquidación de beneficios sociales (finiquito) según la legislación laboral boliviana.

## 📋 Descripción

Aplicación web desarrollada en Streamlit que automatiza el proceso completo de cálculo de finiquitos, desde la carga de datos de planilla hasta la generación de documentos Excel editables con opciones de sellado QR interno.

## ✨ Características Principales

- **Carga Flexible de Datos**: Importación de 3 meses de planilla + base de datos RDP
- **Mapeo Inteligente**: Configuración dinámica de columnas con homologación de empresas
- **Cálculo Preciso**: Motor de cálculo determinístico equivalente a Excel
- **Generación de Documentos**: 6 tipos de documentos con plantillas personalizables
- **Sellado QR Opcional**: Estampado interno configurable por documento
- **Gestión de Casos**: Historial completo con búsqueda y filtrado avanzado
- **Panel Administrativo**: Configuración de reglas, plantillas y usuarios
- **Auditoría Completa**: Registro de todas las acciones del sistema

## 🚀 Instalación Rápida

### Prerrequisitos

- Python 3.11 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**
```bash
cd /path/to/finiquito_app
```

2. **Crear entorno virtual (recomendado)**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Inicializar la base de datos**
```bash
python scripts/init_database.py
```

5. **Generar datos de prueba (opcional)**
```bash
python scripts/generate_templates.py
python scripts/generate_test_data.py
```

6. **Ejecutar la aplicación**
```bash
streamlit run main.py
```

La aplicación estará disponible en: http://localhost:8501

## 🔑 Acceso al Sistema

### Usuarios por Defecto

| Usuario  | Contraseña | Rol      | Permisos                              |
|----------|------------|----------|---------------------------------------|
| admin    | admin123   | Admin    | Acceso completo                      |
| operator | oper123    | Operador | Crear casos, generar documentos      |
| viewer   | view123    | Visor    | Solo lectura                         |

## 📁 Estructura del Proyecto

```
finiquito_app/
├── main.py                    # Punto de entrada principal
├── requirements.txt           # Dependencias del proyecto
├── app/
│   ├── pages/                # Páginas de Streamlit
│   │   ├── upload_page.py
│   │   ├── mapping_page.py
│   │   ├── case_selection_page.py
│   │   ├── preview_page.py
│   │   ├── generate_page.py
│   │   ├── case_history_page.py
│   │   ├── case_detail_page.py
│   │   └── admin_page.py
│   └── auth/                  # Autenticación
│       └── auth_handler.py
├── domain/                    # Lógica de negocio
│   ├── entities.py
│   ├── calculator.py
│   └── validators.py
├── infra/                     # Infraestructura
│   ├── database/
│   │   ├── connection.py
│   │   └── models.py
│   ├── excel/
│   │   ├── excel_adapter.py
│   │   └── excel_reader.py
│   └── qr/
│       └── qr_generator.py
├── storage/                   # Almacenamiento
│   ├── uploads/              # Archivos cargados
│   ├── outputs/              # Documentos generados
│   └── templates/            # Plantillas Excel
├── test_data/                # Datos de prueba
└── scripts/                  # Scripts utilitarios
```

## 📊 Flujo de Trabajo

### Proceso Principal (5 pasos)

1. **Cargar Archivos** → Subir 3 planillas + RDP
2. **Mapeo de Columnas** → Configurar correspondencias
3. **Selección de Caso** → Elegir empleado y parámetros
4. **Vista Previa y Cálculo** → Revisar datos y calcular
5. **Generar Documentos** → Crear y descargar archivos

### Gestión de Casos

- **Historial**: Búsqueda, filtros, estadísticas
- **Detalle**: Vista completa con edición de metadata
- **Administración**: Configuración del sistema

## 📄 Documentos Generados

1. **F_Finiquito**: Liquidación principal (sin sello)
2. **Memo_Finalización**: Memorándum con CITE opcional
3. **F_Salida**: Formulario de salida con checklist
4. **F_Equipos**: Entrega de equipos
5. **Contable_Preview**: Vista contable (sin códigos)
6. **Rechazo_Post**: Notificación post-examen

## ⚙️ Configuración Avanzada

### Base de Datos

Por defecto usa SQLite. Para PostgreSQL:

1. Instalar driver: `pip install psycopg2-binary`
2. Modificar `infra/database/connection.py`:
```python
DATABASE_URL = "postgresql://user:pass@localhost/finiquito_db"
```

### Plantillas Personalizadas

1. Acceder al panel Admin → Plantillas
2. Cargar nueva plantilla Excel
3. Usar placeholders: `{{nombre}}`, `{{ci}}`, etc.
4. Activar versión deseada

### Homologación de Empresas

Configurar variaciones de nombres en Admin → Homologación:
- "ALIANZA SEGUROS S.A." ← "Alianza Seguros SA"
- "ALIANZA VIDA S.A." ← "Alianza Vida SA"

## 🧪 Testing

### Ejecutar Tests Unitarios
```bash
python -m pytest tests/ -v
```

### Datos de Prueba

Los archivos en `test_data/` contienen:
- 5 empleados de ejemplo
- 3 meses de planilla
- Base RDP completa
- Variaciones para probar homologación

## 🔧 Desarrollo

### Agregar Nueva Página

1. Crear archivo en `app/pages/`
2. Implementar función `render_[page]_page()`
3. Registrar en `main.py` → `PAGES`

### Agregar Nuevo Documento

1. Extender `infra/excel/excel_adapter.py`
2. Crear método `create_[document]_file()`
3. Agregar a `generate_page.py`

### Modificar Cálculos

1. Editar `domain/calculator.py`
2. Actualizar tests en `tests/test_calculator.py`
3. Verificar con datos reales

## 📝 Validaciones Implementadas

- ✅ Empleado existe en los 3 meses
- ✅ Empleado existe en RDP
- ✅ Total Ganado = Haber Básico + Bonos
- ✅ Campos requeridos presentes
- ✅ Fechas coherentes
- ✅ Montos positivos

## 🔐 Seguridad

- Autenticación por usuario/contraseña
- Roles y permisos granulares
- Auditoría de todas las acciones
- Hashing de archivos para integridad
- QR con payload verificable

## 🚨 Solución de Problemas

### La aplicación no inicia
```bash
# Verificar dependencias
pip install -r requirements.txt --upgrade

# Reiniciar base de datos
rm finiquito.db  # Solo desarrollo
python scripts/init_database.py
```

### Error al cargar archivos
- Verificar formato Excel (.xlsx)
- Revisar nombres de columnas
- Confirmar encoding UTF-8

### Cálculos incorrectos
- Verificar mapeo de columnas
- Revisar configuración de motivo de retiro
- Comprobar fechas ingresadas

## 📞 Soporte

Para soporte técnico o consultas sobre el sistema:
- Documentación técnica: `/docs`
- Scripts de utilidad: `/scripts`
- Logs del sistema: Verificar consola de Streamlit

## 🏗️ Roadmap

### Próximas Características
- [ ] Exportación a PDF
- [ ] Procesamiento por lotes
- [ ] API REST para integración
- [ ] Notificaciones por email
- [ ] Dashboard gerencial
- [ ] Backup automático

## 📄 Licencia

Sistema propietario desarrollado para Alianza Seguros S.A.

---

**Versión**: 1.0.0  
**Última actualización**: Diciembre 2025  
**Desarrollado por**: JELB - Jefe Nacional de Talento Humano

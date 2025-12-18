#!/usr/bin/env python3
"""
Script de Validación Automática - Sistema de Finiquitos
Verifica que todos los componentes estén instalados y funcionando correctamente
"""

import sys
import os
from pathlib import Path
import importlib.util

# ANSI Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
ENDC = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BOLD}{BLUE}{'='*70}{ENDC}")
    print(f"{BOLD}{BLUE}{text:^70}{ENDC}")
    print(f"{BOLD}{BLUE}{'='*70}{ENDC}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{ENDC}")

def print_error(text):
    print(f"{RED}❌ {text}{ENDC}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{ENDC}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{ENDC}")

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} (Se requiere 3.8+)")
        return False

def check_module(module_name, package_name=None):
    """Check if a Python module is installed"""
    try:
        if package_name is None:
            package_name = module_name
        
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            module = importlib.import_module(module_name)
            version = getattr(module, '__version__', 'unknown')
            print_success(f"{package_name:20s} - versión {version}")
            return True
        else:
            print_error(f"{package_name:20s} - NO INSTALADO")
            return False
    except Exception as e:
        print_error(f"{package_name:20s} - Error: {str(e)}")
        return False

def check_file_structure():
    """Check if all required files and directories exist"""
    base_dir = Path(__file__).parent
    
    required_files = [
        'main.py',
        'config.py',
        'requirements.txt',
        'app/auth/auth_handler.py',
        'domain/calculator.py',
        'domain/entities.py',
        'domain/validators.py',
        'infra/database/connection.py',
        'infra/database/models.py',
        'infra/excel/excel_adapter.py',
        'infra/qr/qr_generator.py'
    ]
    
    required_dirs = [
        'storage/uploads',
        'storage/outputs',
        'storage/templates',
        'test_data'
    ]
    
    all_exist = True
    
    # Check files
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print_success(f"Archivo: {file_path}")
        else:
            print_error(f"Archivo FALTANTE: {file_path}")
            all_exist = False
    
    # Check directories
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if full_path.exists():
            print_success(f"Directorio: {dir_path}")
        else:
            print_error(f"Directorio FALTANTE: {dir_path}")
            all_exist = False
    
    return all_exist

def check_templates():
    """Check if all Excel templates exist"""
    base_dir = Path(__file__).parent
    templates_dir = base_dir / 'storage' / 'templates'
    
    required_templates = [
        'f_finiquito_template.xlsx',
        'memo_finalizacion_template.xlsx',
        'f_salida_template.xlsx',
        'f_equipos_template.xlsx',
        'contable_preview_template.xlsx',
        'rechazo_post_template.xlsx'
    ]
    
    all_exist = True
    
    for template in required_templates:
        template_path = templates_dir / template
        if template_path.exists():
            size = template_path.stat().st_size
            print_success(f"Plantilla: {template:35s} ({size:,} bytes)")
        else:
            print_error(f"Plantilla FALTANTE: {template}")
            all_exist = False
    
    return all_exist

def check_test_data():
    """Check if test data files exist"""
    base_dir = Path(__file__).parent
    test_data_dir = base_dir / 'test_data'
    
    required_files = [
        'planilla_2025_09_mes1.xlsx',
        'planilla_2025_10_mes2.xlsx',
        'planilla_2025_11_mes3.xlsx',
        'rdp_personal.xlsx'
    ]
    
    all_exist = True
    
    for file_name in required_files:
        file_path = test_data_dir / file_name
        if file_path.exists():
            size = file_path.stat().st_size
            print_success(f"Datos: {file_name:30s} ({size:,} bytes)")
        else:
            print_error(f"Datos FALTANTES: {file_name}")
            all_exist = False
    
    return all_exist

def check_pages():
    """Check if all Streamlit pages exist"""
    base_dir = Path(__file__).parent
    pages_dir = base_dir / 'app' / 'pages'
    
    required_pages = [
        'upload_page.py',
        'mapping_page.py',
        'case_selection_page.py',
        'preview_page.py',
        'generate_page.py',
        'case_history_page.py',
        'case_detail_page.py',
        'admin_page.py'
    ]
    
    all_exist = True
    
    for page in required_pages:
        page_path = pages_dir / page
        if page_path.exists():
            print_success(f"Página: {page}")
        else:
            print_error(f"Página FALTANTE: {page}")
            all_exist = False
    
    return all_exist

def test_imports():
    """Test critical imports"""
    imports_to_test = [
        ('config', 'settings'),
        ('domain.entities', 'Employee'),
        ('domain.calculator', 'FiniquitoCalculator'),
        ('domain.validators', 'FiniquitoValidator'),
        ('app.auth.auth_handler', 'authenticate_user'),
        ('infra.database.models', 'User'),
        ('infra.excel.excel_adapter', 'ExcelReader'),
        ('infra.qr.qr_generator', 'QRStampGenerator')
    ]
    
    all_success = True
    
    # Add current directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    for module_name, item_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[item_name])
            getattr(module, item_name)
            print_success(f"Import: {module_name}.{item_name}")
        except Exception as e:
            print_error(f"Import FALLIDO: {module_name}.{item_name} - {str(e)}")
            all_success = False
    
    return all_success

def check_database():
    """Check if database can be initialized"""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from infra.database.connection import init_database
        
        init_database()
        print_success("Base de datos inicializada correctamente")
        
        # Check if database file exists
        db_path = Path(__file__).parent / 'finiquito_app.db'
        if db_path.exists():
            size = db_path.stat().st_size
            print_success(f"Archivo BD: finiquito_app.db ({size:,} bytes)")
        
        return True
    except Exception as e:
        print_error(f"Error inicializando base de datos: {str(e)}")
        return False

def generate_report(results):
    """Generate final validation report"""
    print_header("RESUMEN DE VALIDACIÓN")
    
    total_checks = len(results)
    passed_checks = sum(1 for r in results.values() if r)
    
    print(f"\n{BOLD}Resultado:{ENDC}")
    print(f"  Total de verificaciones: {total_checks}")
    print(f"  {GREEN}Exitosas: {passed_checks}{ENDC}")
    print(f"  {RED}Fallidas: {total_checks - passed_checks}{ENDC}")
    
    percentage = (passed_checks / total_checks) * 100
    
    print(f"\n{BOLD}Porcentaje de éxito: ", end="")
    if percentage == 100:
        print(f"{GREEN}{percentage:.1f}%{ENDC}")
    elif percentage >= 80:
        print(f"{YELLOW}{percentage:.1f}%{ENDC}")
    else:
        print(f"{RED}{percentage:.1f}%{ENDC}")
    
    if percentage == 100:
        print(f"\n{GREEN}{BOLD}🎉 ¡VALIDACIÓN COMPLETADA EXITOSAMENTE!{ENDC}")
        print(f"{GREEN}La aplicación está lista para ejecutarse.{ENDC}")
        print(f"\n{BOLD}Para iniciar la aplicación:{ENDC}")
        print(f"  {BLUE}streamlit run main.py{ENDC}")
    elif percentage >= 80:
        print(f"\n{YELLOW}{BOLD}⚠️  VALIDACIÓN PARCIALMENTE EXITOSA{ENDC}")
        print(f"{YELLOW}La aplicación puede funcionar, pero hay advertencias.{ENDC}")
        print(f"\n{BOLD}Revisa los errores y ejecuta:{ENDC}")
        print(f"  {BLUE}pip install -r requirements.txt{ENDC}")
    else:
        print(f"\n{RED}{BOLD}❌ VALIDACIÓN FALLIDA{ENDC}")
        print(f"{RED}Hay problemas críticos que deben resolverse.{ENDC}")
        print(f"\n{BOLD}Pasos sugeridos:{ENDC}")
        print(f"  1. {BLUE}pip install -r requirements.txt{ENDC}")
        print(f"  2. Verifica que todos los archivos estén presentes")
        print(f"  3. Ejecuta este script nuevamente")

def main():
    """Main validation function"""
    print_header("VALIDACIÓN DEL SISTEMA DE FINIQUITOS")
    print_info("Iniciando verificación de componentes...")
    
    results = {}
    
    # 1. Check Python version
    print_header("1. VERSIÓN DE PYTHON")
    results['python_version'] = check_python_version()
    
    # 2. Check required Python modules
    print_header("2. DEPENDENCIAS DE PYTHON")
    required_modules = [
        ('streamlit', 'Streamlit'),
        ('pandas', 'Pandas'),
        ('openpyxl', 'OpenPyXL'),
        ('pydantic', 'Pydantic'),
        ('qrcode', 'QRCode'),
        ('PIL', 'Pillow'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('dateutil', 'python-dateutil')
    ]
    
    module_results = []
    for module, package in required_modules:
        module_results.append(check_module(module, package))
    results['python_modules'] = all(module_results)
    
    # 3. Check file structure
    print_header("3. ESTRUCTURA DE ARCHIVOS")
    results['file_structure'] = check_file_structure()
    
    # 4. Check Streamlit pages
    print_header("4. PÁGINAS DE STREAMLIT")
    results['pages'] = check_pages()
    
    # 5. Check Excel templates
    print_header("5. PLANTILLAS EXCEL")
    results['templates'] = check_templates()
    
    # 6. Check test data
    print_header("6. DATOS DE PRUEBA")
    results['test_data'] = check_test_data()
    
    # 7. Test imports
    print_header("7. VERIFICACIÓN DE IMPORTS")
    results['imports'] = test_imports()
    
    # 8. Check database
    print_header("8. BASE DE DATOS")
    results['database'] = check_database()
    
    # Generate final report
    generate_report(results)
    
    # Return exit code
    sys.exit(0 if all(results.values()) else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Validación interrumpida por el usuario{ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{RED}Error inesperado: {str(e)}{ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

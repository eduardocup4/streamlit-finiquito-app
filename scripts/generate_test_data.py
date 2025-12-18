"""
Generate Sample Payroll and RDP Data for Testing
Creates realistic test data files for the Finiquito application
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import random

# Create test data directory
TEST_DATA_DIR = Path("/home/claude/finiquito_app/test_data")
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Sample employee data
EMPLOYEES = [
    {"nombre": "Juan Carlos Mendoza López", "ci": "4567890", "ext": "SC"},
    {"nombre": "María Elena Vargas Castro", "ci": "5678901", "ext": "LP"},
    {"nombre": "Roberto Fernández Quiroga", "ci": "6789012", "ext": "CB"},
    {"nombre": "Ana Patricia Rojas Salinas", "ci": "7890123", "ext": "SC"},
    {"nombre": "Carlos Alberto Gutiérrez", "ci": "8901234", "ext": "OR"},
]

EMPRESAS = [
    "ALIANZA SEGUROS S.A.",
    "ALIANZA VIDA S.A.",
    "Alianza Seguros SA",  # Variation for homologation testing
]

UNIDADES = [
    "Gerencia General",
    "Gerencia Técnica",
    "Gerencia Comercial",
    "Gerencia de Operaciones",
    "Gerencia Administrativa",
]

OCUPACIONES = [
    "Gerente de Área",
    "Jefe de Departamento",
    "Analista Senior",
    "Analista Junior",
    "Asistente Administrativo",
]

def generate_payroll_month(month_date: datetime, month_name: str):
    """Generate a payroll month Excel file"""
    
    data = []
    
    for emp in EMPLOYEES:
        # Random variations in empresa name for testing homologation
        empresa = random.choice(EMPRESAS)
        
        # Generate salary components
        haber_basico = random.randint(3000, 15000)
        antiguedad_years = random.randint(0, 15)
        bono_antiguedad = int(haber_basico * 0.05 * min(antiguedad_years, 3))  # 5% per year, max 3 years
        otros_bonos = random.choice([0, 500, 1000, 1500]) if random.random() > 0.5 else 0
        
        total_ganado = haber_basico + bono_antiguedad + otros_bonos
        
        # Calculate dates
        fecha_ingreso = datetime.now() - timedelta(days=365 * antiguedad_years + random.randint(0, 364))
        fecha_nacimiento = datetime.now() - timedelta(days=365 * random.randint(25, 55))
        
        row = {
            "Empresa": empresa,
            "Unidad de Negocio": random.choice(UNIDADES),
            "Ocup. que Desempeña": random.choice(OCUPACIONES),
            "Nro. Doc": emp["ci"],
            "Nombre": emp["nombre"],
            "FechaIngreso": fecha_ingreso.strftime("%Y-%m-%d"),
            "FechaNacimiento": fecha_nacimiento.strftime("%Y-%m-%d"),
            "HaberBasico": haber_basico,
            "BonoAntiguedad": bono_antiguedad,
            "Otros Bonos": otros_bonos,
            "TotalGanado": total_ganado,
            "AFP": int(total_ganado * 0.1271),  # 12.71% AFP
            "RC-IVA": int(total_ganado * 0.13) if total_ganado > 8000 else 0,
            "Otros Descuentos": random.choice([0, 100, 200]) if random.random() > 0.7 else 0,
            "Líquido Pagable": total_ganado - int(total_ganado * 0.1271) - (int(total_ganado * 0.13) if total_ganado > 8000 else 0),
        }
        
        data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to Excel with multiple sheets (to test sheet selection)
    file_path = TEST_DATA_DIR / f"planilla_{month_name}.xlsx"
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Planilla', index=False)
        
        # Add a summary sheet
        summary = pd.DataFrame({
            'Mes': [month_name],
            'Total Empleados': [len(EMPLOYEES)],
            'Total Planilla': [df['TotalGanado'].sum()],
            'Promedio Salarial': [df['TotalGanado'].mean()]
        })
        summary.to_excel(writer, sheet_name='Resumen', index=False)
    
    print(f"Created: {file_path}")
    return file_path

def generate_rdp_file():
    """Generate RDP (personal data) Excel file"""
    
    data = []
    
    estados_civiles = ["Soltero(a)", "Casado(a)", "Divorciado(a)", "Viudo(a)"]
    ciudades = ["Santa Cruz", "La Paz", "Cochabamba", "Oruro", "Potosí"]
    
    for emp in EMPLOYEES:
        # Use consistent empresa for RDP
        empresa = EMPRESAS[0]  # Main company name
        
        row = {
            "Empresa": empresa,
            "Nro. Doc": emp["ci"],
            "Extension": emp["ext"],
            "Nombre Completo": emp["nombre"],
            "EstadoCivil": random.choice(estados_civiles),
            "Domicilio": f"{random.choice(['Av.', 'Calle'])} {random.randint(1, 20)} #{random.randint(100, 999)}, {random.choice(ciudades)}",
            "Telefono": f"{random.randint(60000000, 79999999)}",
            "Email": f"{emp['nombre'].split()[0].lower()}.{emp['nombre'].split()[-1].lower()}@alianza.com.bo",
            "Contacto Emergencia": f"Familiar - {random.randint(60000000, 79999999)}",
            "Grupo Sanguineo": random.choice(["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]),
        }
        
        data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to Excel
    file_path = TEST_DATA_DIR / "rdp_personal.xlsx"
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='RDP', index=False)
        
        # Add metadata sheet
        metadata = pd.DataFrame({
            'Campo': ['Fecha Generación', 'Total Registros', 'Sistema'],
            'Valor': [datetime.now().strftime("%Y-%m-%d"), len(EMPLOYEES), 'SAP']
        })
        metadata.to_excel(writer, sheet_name='Metadata', index=False)
    
    print(f"Created: {file_path}")
    return file_path

def generate_test_files():
    """Generate all test files"""
    print("Generating Test Data Files...")
    print("=" * 50)
    
    # Generate 3 months of payroll
    today = datetime.now()
    
    # Month 1 (3 months ago)
    month1_date = today - timedelta(days=90)
    month1_name = month1_date.strftime("%Y_%m") + "_mes1"
    file1 = generate_payroll_month(month1_date, month1_name)
    
    # Month 2 (2 months ago)
    month2_date = today - timedelta(days=60)
    month2_name = month2_date.strftime("%Y_%m") + "_mes2"
    file2 = generate_payroll_month(month2_date, month2_name)
    
    # Month 3 (1 month ago)
    month3_date = today - timedelta(days=30)
    month3_name = month3_date.strftime("%Y_%m") + "_mes3"
    file3 = generate_payroll_month(month3_date, month3_name)
    
    # Generate RDP file
    rdp_file = generate_rdp_file()
    
    print("=" * 50)
    print("✅ Test data files created successfully!")
    print(f"Location: {TEST_DATA_DIR}")
    print("\nFiles created:")
    print(f"  - {file1.name} (Mes 1)")
    print(f"  - {file2.name} (Mes 2)")
    print(f"  - {file3.name} (Mes 3)")
    print(f"  - {rdp_file.name} (RDP)")
    
    # Create info file
    info_path = TEST_DATA_DIR / "test_data_info.txt"
    with open(info_path, 'w') as f:
        f.write("Test Data for Finiquito System\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write("=" * 50 + "\n\n")
        f.write("Employees in test data:\n")
        for emp in EMPLOYEES:
            f.write(f"  - {emp['nombre']} (CI: {emp['ci']})\n")
        f.write("\n")
        f.write("Files:\n")
        f.write(f"  - Payroll Month 1: {file1.name}\n")
        f.write(f"  - Payroll Month 2: {file2.name}\n")
        f.write(f"  - Payroll Month 3: {file3.name}\n")
        f.write(f"  - RDP Data: {rdp_file.name}\n")
        f.write("\n")
        f.write("Notes:\n")
        f.write("  - Empresa names have variations to test homologation\n")
        f.write("  - Each payroll file has 'Planilla' and 'Resumen' sheets\n")
        f.write("  - RDP file has 'RDP' and 'Metadata' sheets\n")
        f.write("  - Total_Ganado = Haber_Basico + Bono_Antiguedad + Otros_Bonos\n")
    
    print(f"\nInfo file: {info_path}")
    
    return [file1, file2, file3, rdp_file]

if __name__ == "__main__":
    generate_test_files()

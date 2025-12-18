"""
Configuración principal de la aplicación de Finiquitos Bolivia
"""
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import Field
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for pydantic v1
    from pydantic import BaseSettings

# Paths configuration (Variables Globales)
BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
OUTPUTS_DIR = STORAGE_DIR / "outputs"
TEMPLATES_DIR = STORAGE_DIR / "templates"

# Create directories if they don't exist
for directory in [STORAGE_DIR, UPLOADS_DIR, OUTPUTS_DIR, TEMPLATES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    """Application settings"""
    
    # --- CORRECCIÓN CRÍTICA: Exponer rutas en la clase Settings ---
    # Estas líneas conectan las variables de arriba con la clase
    BASE_DIR: Path = BASE_DIR
    STORAGE_DIR: Path = STORAGE_DIR
    UPLOADS_DIR: Path = UPLOADS_DIR
    OUTPUTS_DIR: Path = OUTPUTS_DIR
    TEMPLATES_DIR: Path = TEMPLATES_DIR
    # -------------------------------------------------------------

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./finiquito_app.db",
        env="DATABASE_URL"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production",
        env="SECRET_KEY"
    )
    ADMIN_PASSWORD: str = Field(
        default="admin123",
        env="ADMIN_PASSWORD"
    )
    
    # Application
    APP_NAME: str = "Sistema de Cálculo de Finiquitos"
    APP_VERSION: str = "1.0.0"
    COMPANY_NAME: str = "JELB Solutions"
    
    # Excel processing
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = [".xlsx", ".xls"]
    
    # Calculation parameters
    MONTHS_FOR_AVERAGE: int = 3
    DAYS_IN_MONTH: int = 30
    DAYS_IN_YEAR: int = 360
    
    # Document generation
    ENABLE_QR_STAMP: bool = True
    QR_STAMP_TEXT: str = "Diseñado por JELB"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Bolivian labor law constants
class BolivianLaborConstants:
    """Constants for Bolivian labor law calculations"""
    
    # Minimum wage (update as needed)
    MINIMUM_WAGE = 2362.00  # Bolivianos
    
    # UFV (Unidad de Fomento a la Vivienda) - Update regularly
    UFV_VALUE = 2.43  # Example value
    
    # Benefit calculation factors
    INDEMNIZATION_MONTHS = 1  # Per year
    DESAHUCIO_MONTHS = 1  # Per year
    AGUINALDO_MONTHS = 1  # Per year (duodécimas)
    VACATION_DAYS_MIN = 15  # Minimum vacation days
    VACATION_DAYS_5_YEARS = 20  # After 5 years
    VACATION_DAYS_10_YEARS = 30  # After 10 years
    
    # Quinquenio thresholds
    QUINQUENIO_YEARS = 5
    QUINQUENIO_PERCENTAGES = {
        5: 5,    # 5% after 5 years
        10: 11,  # 11% after 10 years
        15: 18,  # 18% after 15 years
        20: 26,  # 26% after 20 years
        25: 34   # 34% after 25 years
    }
    
    # Motivos de retiro
    MOTIVO_RETIRO_TYPES = {
        "RENUNCIA": {
            "description": "Renuncia voluntaria",
            "dia_menos_flag": False,
            "indemnizacion_flag": True, 
            "aguinaldo_flag": True,
            "desahucio_flag": False,
            "vacaciones_flag": True
        },
        "DESPIDO": {
            "description": "Despido con causa justificada",
            "dia_menos_flag": True,
            "indemnizacion_flag": False,
            "aguinaldo_flag": True,
            "desahucio_flag": False,
            "vacaciones_flag": True
        },
        "DESPIDO_INJUSTIFICADO": {
            "description": "Despido sin causa justificada",
            "dia_menos_flag": False,
            "indemnizacion_flag": True,
            "aguinaldo_flag": True,
            "desahucio_flag": True,
            "vacaciones_flag": True
        },
        "RETIRO_INDIRECTO": {
            "description": "Retiro indirecto",
            "dia_menos_flag": False,
            "indemnizacion_flag": True,
            "aguinaldo_flag": True,
            "desahucio_flag": True,
            "vacaciones_flag": True
        },
        "QUINQUENIO": {
            "description": "Retiro por quinquenio",
            "dia_menos_flag": False,
            "indemnizacion_flag": True,
            "aguinaldo_flag": False,
            "desahucio_flag": False,
            "vacaciones_flag": False
        },
        "CONCLUSION_CONTRATO": {
            "description": "Conclusión de contrato",
            "dia_menos_flag": False,
            "indemnizacion_flag": True,
            "aguinaldo_flag": True,
            "desahucio_flag": False,
            "vacaciones_flag": True
        }
    }

# Field mapping configuration
class FieldMappingConfig:
    """Configuration for field mapping between different Excel formats"""
    
    REQUIRED_PAYROLL_FIELDS = [
        "nombre",
        "empresa",
        "ci",
        "unidad",
        "ocupacion",
        "fecha_ingreso",
        "fecha_nacimiento",
        "haber_basico",
        "bono_antiguedad",
        "total_ganado"
    ]
    
    REQUIRED_RDP_FIELDS = [
        "empresa",
        "ci",
        "extension",
        "estado_civil",
        "domicilio"
    ]
    
    # Common column name variations
    FIELD_ALIASES = {
        "ci": ["ci", "nro_doc", "documento", "cedula", "carnet"],
        "nombre": ["nombre", "nombres", "nombre_completo", "empleado"],
        "empresa": ["empresa", "compañia", "company", "sociedad"],
        "unidad": ["unidad", "unidad_negocio", "departamento", "area"],
        "ocupacion": ["ocupacion", "cargo", "puesto", "posicion"],
        "fecha_ingreso": ["fecha_ingreso", "fecha_inicio", "fecha_contrato", "ingreso"],
        "fecha_nacimiento": ["fecha_nacimiento", "fecha_nac", "nacimiento"],
        "haber_basico": ["haber_basico", "salario_base", "sueldo_basico", "basico"],
        "bono_antiguedad": ["bono_antiguedad", "antiguedad", "bono_ant"],
        "total_ganado": ["total_ganado", "total", "total_mes", "ganado"],
        "otros_bonos": ["otros_bonos", "otros", "bonos_adicionales", "bonos"],
        "extension": ["extension", "ext", "expedido"],
        "estado_civil": ["estado_civil", "civil", "est_civil"],
        "domicilio": ["domicilio", "direccion", "address", "dir"]
    }

settings = Settings()
labor_constants = BolivianLaborConstants()
field_config = FieldMappingConfig()
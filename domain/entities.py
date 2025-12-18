"""
Domain entities for the finiquito calculation system
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, Dict, List, Any
from decimal import Decimal
import uuid

@dataclass
class Employee:
    """Employee entity with all required information"""
    ci: str
    name: str
    empresa: str
    unidad: str
    ocupacion: str
    fecha_ingreso: date
    fecha_nacimiento: date
    extension: Optional[str] = None
    estado_civil: Optional[str] = None
    domicilio: Optional[str] = None
    
    def __post_init__(self):
        if isinstance(self.fecha_ingreso, str):
            self.fecha_ingreso = datetime.strptime(self.fecha_ingreso, "%Y-%m-%d").date()
        if isinstance(self.fecha_nacimiento, str):
            self.fecha_nacimiento = datetime.strptime(self.fecha_nacimiento, "%Y-%m-%d").date()
    
    @property
    def full_identifier(self) -> str:
        return f"{self.ci}_{self.empresa}"

@dataclass
class PayrollMonth:
    month_name: str
    year_month: str
    haber_basico: Decimal
    bono_antiguedad: Decimal
    otros_bonos: Optional[Decimal] = None
    total_ganado: Decimal = Decimal(0)
    
    def __post_init__(self):
        self.haber_basico = Decimal(str(self.haber_basico))
        self.bono_antiguedad = Decimal(str(self.bono_antiguedad))
        if self.otros_bonos:
            self.otros_bonos = Decimal(str(self.otros_bonos))
        self.total_ganado = Decimal(str(self.total_ganado))

@dataclass
class Antiguedad:
    years: int
    months: int
    days: int
    total_days: int
    
    @property
    def formatted(self) -> str:
        return f"{self.years} años, {self.months} meses, {self.days} días"

@dataclass
class ManualInputs:
    """Manual inputs for calculation"""
    vacation_days_balance: Decimal = Decimal(0)
    rc_iva_flag: bool = False
    
    # Nuevos campos para Bono Extraordinario
    bono_extraordinario_monto: Decimal = Decimal(0)
    bono_extraordinario_label: str = ""
    
    # Campos existentes
    otros_conceptos: List[Dict[str, Any]] = None
    deducciones: List[Dict[str, Any]] = None
    anticipos: List[Dict[str, Any]] = None
    
    # Obsoletos (mantenidos por compatibilidad temporal si es necesario)
    bono_refrigerio: Decimal = Decimal(0)
    comision_neta_ffvv: Decimal = Decimal(0)
    
    def __post_init__(self):
        self.vacation_days_balance = Decimal(str(self.vacation_days_balance))
        self.bono_extraordinario_monto = Decimal(str(self.bono_extraordinario_monto))
        if self.otros_conceptos is None: self.otros_conceptos = []
        if self.deducciones is None: self.deducciones = []
        if self.anticipos is None: self.anticipos = []

@dataclass
class CaseParameters:
    pay_until_date: date
    request_date: date
    motivo_retiro: str
    calculation_start_date: date
    quinquenio_start_date: Optional[date] = None
    aguinaldo_already_paid: bool = False
    
    def __post_init__(self):
        if isinstance(self.pay_until_date, str):
            self.pay_until_date = datetime.strptime(self.pay_until_date, "%Y-%m-%d").date()
        if isinstance(self.calculation_start_date, str):
             self.calculation_start_date = datetime.strptime(self.calculation_start_date, "%Y-%m-%d").date()
        if isinstance(self.request_date, str):
            self.request_date = datetime.strptime(self.request_date, "%Y-%m-%d").date()
        if self.quinquenio_start_date and isinstance(self.quinquenio_start_date, str):
            self.quinquenio_start_date = datetime.strptime(self.quinquenio_start_date, "%Y-%m-%d").date()

@dataclass
class BenefitCalculation:
    concept: str
    description: str
    base_amount: Decimal
    factor: Optional[Decimal] = None
    days: Optional[int] = None
    months: Optional[int] = None
    years: Optional[int] = None
    calculated_amount: Decimal = Decimal(0)
    
    def __post_init__(self):
        self.base_amount = Decimal(str(self.base_amount))
        if self.factor: self.factor = Decimal(str(self.factor))
        self.calculated_amount = Decimal(str(self.calculated_amount))

@dataclass
class FiniquitoCalculationResult:
    calculation_id: str
    employee: Employee
    case_params: CaseParameters
    antiguedad: Antiguedad
    tiempo_pago: Antiguedad
    payroll_months: List[PayrollMonth]
    salary_average: Decimal
    manual_inputs: ManualInputs
    benefits: List[BenefitCalculation]
    deductions: List[BenefitCalculation]
    total_benefits: Decimal
    total_deductions: Decimal
    net_payment: Decimal
    calculation_date: datetime
    motivo_config: Dict[str, Any]
    
    def __post_init__(self):
        if not self.calculation_id: self.calculation_id = str(uuid.uuid4())
        self.salary_average = Decimal(str(self.salary_average))
        self.total_benefits = Decimal(str(self.total_benefits))
        self.total_deductions = Decimal(str(self.total_deductions))
        self.net_payment = Decimal(str(self.net_payment))

@dataclass
class ValidationResult:
    validation_id: str
    is_valid: bool
    severity: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    @property
    def is_blocking(self) -> bool:
        return self.severity == 'blocking' and not self.is_valid
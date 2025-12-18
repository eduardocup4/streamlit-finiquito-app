"""
Data validators for finiquito calculation
"""
from typing import List, Dict, Any, Optional
from datetime import date
from decimal import Decimal
import hashlib
import json

from domain.entities import (
    Employee, PayrollMonth, ValidationResult, 
    CaseParameters, ManualInputs
)

class FiniquitoValidator:
    """Validator for finiquito calculation data"""
    def validate_pay_date_after_ingreso(
        self,
        fecha_ingreso: date,
        pay_until_date: date
    ) -> ValidationResult:
        """
        Validate that pay date is after admission date (Method required by preview_page)
        """
        if pay_until_date < fecha_ingreso:
            return ValidationResult(
                validation_id="pay_date_after_ingreso",
                is_valid=False,
                severity="blocking",
                message="La fecha de retiro es anterior a la fecha de ingreso",
                details={
                    "fecha_ingreso": fecha_ingreso.isoformat(),
                    "pay_until_date": pay_until_date.isoformat()
                }
            )
        return ValidationResult(
            validation_id="pay_date_after_ingreso",
            is_valid=True,
            severity="info",
            message="Fechas consistentes",
            details={}
        )
    def validate_employee_exists_all_months(
        self,
        employee_ci: str,
        employee_empresa: str,
        payroll_data_months: List[Dict[str, Any]]
    ) -> ValidationResult:
        """
        Validate that employee exists in all 3 payroll months
        """
        months_found = []
        months_missing = []
        
        for idx, month_data in enumerate(payroll_data_months, 1):
            found = False
            for _, row in month_data.iterrows():
                if (str(row.get('ci', '')).strip() == employee_ci and 
                    str(row.get('empresa', '')).strip() == employee_empresa):
                    found = True
                    break
            
            if found:
                months_found.append(f"MES{idx}")
            else:
                months_missing.append(f"MES{idx}")
        
        is_valid = len(months_missing) == 0
        
        return ValidationResult(
            validation_id="employee_exists_all_months",
            is_valid=is_valid,
            severity="blocking",
            message=f"Empleado encontrado en: {', '.join(months_found)}" if is_valid 
                   else f"Empleado NO encontrado en: {', '.join(months_missing)}",
            details={
                "months_found": months_found,
                "months_missing": months_missing,
                "ci": employee_ci,
                "empresa": employee_empresa
            }
        )
    
    def validate_employee_in_rdp(
        self,
        employee_ci: str,
        employee_empresa: str,
        rdp_data: Any
    ) -> ValidationResult:
        """
        Validate that employee exists in RDP
        """
        found = False
        rdp_row = None
        
        for _, row in rdp_data.iterrows():
            if (str(row.get('ci', '')).strip() == employee_ci and 
                str(row.get('empresa', '')).strip() == employee_empresa):
                found = True
                rdp_row = row.to_dict()
                break
        
        return ValidationResult(
            validation_id="employee_in_rdp",
            is_valid=found,
            severity="blocking",
            message=f"Empleado {'encontrado' if found else 'NO encontrado'} en RDP",
            details={
                "found": found,
                "rdp_data": rdp_row if found else None,
                "ci": employee_ci,
                "empresa": employee_empresa
            }
        )
    
    def validate_total_ganado(
        self,
        payroll_months: List[PayrollMonth]
    ) -> List[ValidationResult]:
        """
        Validate that TotalGanado matches calculated total for each month
        """
        results = []
        
        for month in payroll_months:
            difference = month.validation_difference
            is_valid = abs(difference) < Decimal('0.01')  # Allow 1 cent difference
            
            results.append(
                ValidationResult(
                    validation_id=f"total_ganado_{month.month_name}",
                    is_valid=is_valid,
                    severity="blocking" if abs(difference) > Decimal('1.00') else "warning",
                    message=f"{month.month_name}: Total {'correcto' if is_valid else f'diferencia de {difference:.2f}'}",
                    details={
                        "month": month.month_name,
                        "declared_total": float(month.total_ganado),
                        "calculated_total": float(month.calculated_total),
                        "difference": float(difference),
                        "components": {
                            "haber_basico": float(month.haber_basico),
                            "bono_antiguedad": float(month.bono_antiguedad),
                            "otros_bonos": float(month.otros_bonos) if month.otros_bonos else 0
                        }
                    }
                )
            )
        
        return results
    
    def validate_required_fields(
        self,
        data_row: Dict[str, Any],
        required_fields: List[str],
        data_source: str
    ) -> ValidationResult:
        """
        Validate that all required fields are present and not empty
        """
        missing_fields = []
        empty_fields = []
        
        for field in required_fields:
            if field not in data_row:
                missing_fields.append(field)
            elif data_row[field] is None or str(data_row[field]).strip() == '':
                empty_fields.append(field)
        
        is_valid = len(missing_fields) == 0 and len(empty_fields) == 0
        
        message = f"Todos los campos requeridos presentes en {data_source}"
        if missing_fields:
            message = f"Campos faltantes en {data_source}: {', '.join(missing_fields)}"
        elif empty_fields:
            message = f"Campos vacíos en {data_source}: {', '.join(empty_fields)}"
        
        return ValidationResult(
            validation_id=f"required_fields_{data_source}",
            is_valid=is_valid,
            severity="blocking",
            message=message,
            details={
                "data_source": data_source,
                "missing_fields": missing_fields,
                "empty_fields": empty_fields,
                "checked_fields": required_fields
            }
        )
    
    def validate_dates(
        self,
        case_params: CaseParameters,
        employee: Employee
    ) -> List[ValidationResult]:
        """
        Validate date logic and consistency
        """
        results = []
        
        # Pay until date should be after fecha ingreso
        if case_params.pay_until_date < employee.fecha_ingreso:
            results.append(
                ValidationResult(
                    validation_id="pay_date_after_ingreso",
                    is_valid=False,
                    severity="blocking",
                    message="Fecha de pago debe ser posterior a fecha de ingreso",
                    details={
                        "fecha_ingreso": employee.fecha_ingreso.isoformat(),
                        "pay_until_date": case_params.pay_until_date.isoformat()
                    }
                )
            )
        else:
            results.append(
                ValidationResult(
                    validation_id="pay_date_after_ingreso",
                    is_valid=True,
                    severity="info",
                    message="Fechas consistentes",
                    details={}
                )
            )
        
        # Request date validation
        if case_params.request_date > date.today():
            results.append(
                ValidationResult(
                    validation_id="request_date_future",
                    is_valid=False,
                    severity="warning",
                    message="Fecha de solicitud es futura",
                    details={
                        "request_date": case_params.request_date.isoformat(),
                        "today": date.today().isoformat()
                    }
                )
            )
        
        # Quinquenio date validation if applicable
        if case_params.quinquenio_start_date:
            if case_params.quinquenio_start_date > case_params.pay_until_date:
                results.append(
                    ValidationResult(
                        validation_id="quinquenio_date_logic",
                        is_valid=False,
                        severity="blocking",
                        message="Fecha de quinquenio debe ser anterior a fecha de pago",
                        details={
                            "quinquenio_start": case_params.quinquenio_start_date.isoformat(),
                            "pay_until_date": case_params.pay_until_date.isoformat()
                        }
                    )
                )
        
        return results
    
    def validate_amounts(
        self,
        payroll_months: List[PayrollMonth],
        manual_inputs: ManualInputs
    ) -> List[ValidationResult]:
        """
        Validate that amounts are reasonable and positive
        """
        results = []
        
        # Check payroll amounts
        for month in payroll_months:
            if month.haber_basico <= 0:
                results.append(
                    ValidationResult(
                        validation_id=f"haber_basico_positive_{month.month_name}",
                        is_valid=False,
                        severity="blocking",
                        message=f"{month.month_name}: Haber básico debe ser positivo",
                        details={"haber_basico": float(month.haber_basico)}
                    )
                )
            
            if month.total_ganado <= 0:
                results.append(
                    ValidationResult(
                        validation_id=f"total_ganado_positive_{month.month_name}",
                        is_valid=False,
                        severity="blocking",
                        message=f"{month.month_name}: Total ganado debe ser positivo",
                        details={"total_ganado": float(month.total_ganado)}
                    )
                )
        
        # Check manual inputs
        if manual_inputs.bono_refrigerio < 0:
            results.append(
                ValidationResult(
                    validation_id="bono_refrigerio_negative",
                    is_valid=False,
                    severity="warning",
                    message="Bono refrigerio no puede ser negativo",
                    details={"bono_refrigerio": float(manual_inputs.bono_refrigerio)}
                )
            )
        
        if manual_inputs.comision_neta_ffvv < 0:
            results.append(
                ValidationResult(
                    validation_id="comision_negative",
                    is_valid=False,
                    severity="warning",
                    message="Comisión no puede ser negativa",
                    details={"comision": float(manual_inputs.comision_neta_ffvv)}
                )
            )
        
        # If all amounts are valid
        if not results:
            results.append(
                ValidationResult(
                    validation_id="amounts_valid",
                    is_valid=True,
                    severity="info",
                    message="Todos los montos son válidos",
                    details={}
                )
            )
        
        return results
    
    def calculate_input_hash(
        self,
        employee: Employee,
        payroll_months: List[PayrollMonth],
        case_params: CaseParameters
    ) -> str:
        """
        Calculate hash of input data for tracking changes
        """
        data_to_hash = {
            "employee_ci": employee.ci,
            "employee_empresa": employee.empresa,
            "pay_until_date": case_params.pay_until_date.isoformat(),
            "motivo_retiro": case_params.motivo_retiro,
            "payroll_data": [
                {
                    "month": pm.month_name,
                    "haber_basico": float(pm.haber_basico),
                    "bono_antiguedad": float(pm.bono_antiguedad),
                    "total_ganado": float(pm.total_ganado)
                }
                for pm in payroll_months
            ]
        }
        
        json_str = json.dumps(data_to_hash, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def run_all_validations(
        self,
        employee: Employee,
        payroll_months: List[PayrollMonth],
        case_params: CaseParameters,
        manual_inputs: ManualInputs,
        payroll_data_months: Optional[List[Dict[str, Any]]] = None,
        rdp_data: Optional[Any] = None
    ) -> tuple[bool, List[ValidationResult]]:
        """
        Run all validations and return overall result
        """
        all_results = []
        
        # Validate dates
        all_results.extend(self.validate_dates(case_params, employee))
        
        # Validate amounts
        all_results.extend(self.validate_amounts(payroll_months, manual_inputs))
        
        # Validate total ganado
        all_results.extend(self.validate_total_ganado(payroll_months))
        
        # Check for blocking validations
        has_blocking = any(r.is_blocking for r in all_results)
        
        return not has_blocking, all_results

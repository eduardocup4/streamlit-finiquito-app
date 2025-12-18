"""
Finiquito calculation engine following Bolivian labor law
"""
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Dict, Any, Union
import uuid

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from domain.entities import (
    Employee, PayrollMonth, Antiguedad, ManualInputs, 
    CaseParameters, BenefitCalculation, FiniquitoCalculationResult
)
from config import BolivianLaborConstants

class FiniquitoCalculator:
    """Calculadora con lógica detallada (Desglose Indemnización, Desahucio x3)"""
    
    def __init__(self):
        self.constants = BolivianLaborConstants()
    
    def _get_config_value(self, config: Any, key: str, default: bool = False) -> bool:
        if isinstance(config, dict): return config.get(key, default)
        return getattr(config, key, default)

    def calculate_antiguedad(self, start_date: date, end_date: date, dia_menos: bool = False) -> Antiguedad:
        """Cálculo genérico de tiempo entre fechas"""
        if dia_menos:
            calc_end = end_date - timedelta(days=1)
        else:
            calc_end = end_date
            
        delta = relativedelta(calc_end, start_date)
        total_days = (delta.years * 360) + (delta.months * 30) + delta.days
        
        return Antiguedad(years=delta.years, months=delta.months, days=delta.days, total_days=total_days)
    
    def calculate_salary_average(self, payroll_months: List[PayrollMonth]) -> Decimal:
        if len(payroll_months) != 3: return Decimal(0)
        total = sum(pm.total_ganado for pm in payroll_months)
        return (total / Decimal('3')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_indemnizacion_step_by_step(
        self, 
        salary_average: Decimal, 
        tiempo_pago: Antiguedad, 
        include: bool = True
    ) -> List[BenefitCalculation]:
        """
        Calcula la indemnización desglosada paso a paso:
        1. Por Años (Sueldo completo)
        2. Por Meses (Duodécimas)
        3. Por Días (Trescientosavos)
        """
        results = []
        if not include:
            return results
        
        # 1. Cálculo por Años
        if tiempo_pago.years > 0:
            monto_anos = salary_average * Decimal(tiempo_pago.years)
            results.append(BenefitCalculation(
                concept="INDEMNIZACION_ANOS",
                description=f"Indemnización: {tiempo_pago.years} Años",
                base_amount=salary_average,
                factor=Decimal(tiempo_pago.years),
                calculated_amount=monto_anos.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            ))
            
        # 2. Cálculo por Meses (Promedio / 12 * Meses)
        if tiempo_pago.months > 0:
            monto_meses = (salary_average / Decimal('12')) * Decimal(tiempo_pago.months)
            results.append(BenefitCalculation(
                concept="INDEMNIZACION_MESES",
                description=f"Indemnización: {tiempo_pago.months} Meses (Duodécimas)",
                base_amount=salary_average,
                months=tiempo_pago.months,
                calculated_amount=monto_meses.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            ))
            
        # 3. Cálculo por Días (Promedio / 360 * Días)
        if tiempo_pago.days > 0:
            monto_dias = (salary_average / Decimal('360')) * Decimal(tiempo_pago.days)
            results.append(BenefitCalculation(
                concept="INDEMNIZACION_DIAS",
                description=f"Indemnización: {tiempo_pago.days} Días (Proporcional)",
                base_amount=salary_average,
                days=tiempo_pago.days,
                calculated_amount=monto_dias.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            ))
            
        return results
    
    def calculate_desahucio(self, salary_average: Decimal, include: bool = False) -> BenefitCalculation:
        """Desahucio: 3 Sueldos promedio por despido intempestivo"""
        if not include: 
            return BenefitCalculation("DESAHUCIO", "Desahucio", Decimal(0), calculated_amount=Decimal(0))
        
        # Cálculo directo: 3 sueldos
        amount = salary_average * Decimal('3')
        
        return BenefitCalculation(
            concept="DESAHUCIO", 
            description="Desahucio (3 Meses de Sueldo)", 
            base_amount=salary_average, 
            factor=Decimal(3), 
            calculated_amount=amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        )
    
    def calculate_aguinaldo(self, salary_average: Decimal, pay_until_date: date, exclude: bool = False) -> BenefitCalculation:
        if exclude:
            return BenefitCalculation("AGUINALDO", "AGUINALDO (Ya fue pagado)", Decimal(0), calculated_amount=Decimal(0))
        
        year_start = date(pay_until_date.year, 1, 1)
        days_worked = (pay_until_date - year_start).days + 1
        proportion = Decimal(days_worked) / Decimal('360')
        amount = salary_average * proportion
        
        return BenefitCalculation("AGUINALDO", f"Aguinaldo Gestión {pay_until_date.year} ({days_worked} días)", salary_average, days=days_worked, factor=proportion, calculated_amount=amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    def calculate_vacaciones_manual(self, salary_average: Decimal, days_balance: Decimal, include: bool = True) -> BenefitCalculation:
        if not include or days_balance <= 0:
            return BenefitCalculation("VACACIONES", "Vacaciones", Decimal(0), calculated_amount=Decimal(0))
        
        daily_salary = salary_average / Decimal('30')
        amount = daily_salary * days_balance
        
        return BenefitCalculation(
            "VACACIONES", 
            f"Vacaciones (Saldo: {days_balance} días)", 
            salary_average, 
            factor=days_balance, 
            calculated_amount=amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        )

    def calculate_prima(self, salary_average: Decimal, tiempo_pago: Antiguedad) -> BenefitCalculation:
        # Prima legal (si corresponde por quinquenio): 25% de 1 sueldo por año
        factor_anos = Decimal(tiempo_pago.years) + (Decimal(tiempo_pago.months)/12) + (Decimal(tiempo_pago.days)/360)
        amount = (salary_average * factor_anos) * Decimal('0.25')
        
        return BenefitCalculation("PRIMA_LEGAL", "Prima Legal (Quinquenio)", salary_average, calculated_amount=amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    def calculate_rc_iva(self, vacation_amount: Decimal, active: bool) -> Optional[BenefitCalculation]:
        if not active or vacation_amount <= 0:
            return None
        amount = vacation_amount * Decimal('0.13')
        return BenefitCalculation(
            "RC_IVA_VACACIONES",
            "RC-IVA (13% sobre Vacaciones)",
            vacation_amount,
            factor=Decimal('0.13'),
            calculated_amount=amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        )

    # (Mantén los imports y métodos helper anteriores igual)
# Solo actualiza el método calculate al final de la clase FiniquitoCalculator

    # ... (métodos calculate_antiguedad, calculate_indemnizacion, etc. IGUAL QUE ANTES) ...

    def calculate(self, employee, payroll_months, case_params, manual_inputs, motivo_config=None) -> FiniquitoCalculationResult:
        # Configuración por defecto
        if not motivo_config:
            class ConfigObj: pass
            motivo_config = ConfigObj()
            motivo_config.indemnizacion_flag = True
            motivo_config.aguinaldo_flag = True
            motivo_config.vacaciones_flag = True
            motivo_config.desahucio_flag = False
            motivo_config.dia_menos_flag = False

        # Leer flags
        dia_menos = self._get_config_value(motivo_config, 'dia_menos_flag')
        indem_flag = self._get_config_value(motivo_config, 'indemnizacion_flag')
        desahucio_flag = self._get_config_value(motivo_config, 'desahucio_flag')
        aguinaldo_flag = self._get_config_value(motivo_config, 'aguinaldo_flag')
        vacaciones_flag = self._get_config_value(motivo_config, 'vacaciones_flag')

        # Refuerzo Lógico (Bolivia)
        is_despido_justificado = "JUSTIFICADO" in str(case_params.motivo_retiro).upper()
        
        # 1. Tiempos
        antiguedad_real = self.calculate_antiguedad(employee.fecha_ingreso, case_params.pay_until_date, dia_menos)
        tiempo_pago = self.calculate_antiguedad(case_params.calculation_start_date, case_params.pay_until_date, dia_menos)
        
        if tiempo_pago.total_days > 90 and not is_despido_justificado:
             indem_flag = True 
        if "DESPIDO" in str(case_params.motivo_retiro).upper() and not is_despido_justificado:
            desahucio_flag = True
        
        # 2. Promedio
        salary_avg = self.calculate_salary_average(payroll_months)
        
        benefits = []
        deductions = []
        
        # --- CÁLCULO BENEFICIOS ---
        
        # A. Indemnización
        indem_items = self.calculate_indemnizacion_step_by_step(salary_avg, tiempo_pago, include=indem_flag)
        if indem_items: benefits.extend(indem_items)
        
        # B. Desahucio
        des = self.calculate_desahucio(salary_avg, include=desahucio_flag)
        if des.calculated_amount > 0: benefits.append(des)
        
        # C. Aguinaldo
        excl_aguinaldo = case_params.aguinaldo_already_paid or not aguinaldo_flag
        ag = self.calculate_aguinaldo(salary_avg, case_params.pay_until_date, exclude=excl_aguinaldo)
        if ag.calculated_amount > 0 or case_params.aguinaldo_already_paid: benefits.append(ag)
            
        # D. Vacaciones
        vac = self.calculate_vacaciones_manual(salary_avg, manual_inputs.vacation_days_balance, include=vacaciones_flag)
        if vac.calculated_amount > 0: benefits.append(vac)
        
        # E. Prima
        if case_params.motivo_retiro == "QUINQUENIO":
            prima = self.calculate_prima(salary_avg, tiempo_pago)
            if prima.calculated_amount > 0: benefits.append(prima)

        # F. Bono Extraordinario (NUEVO)
        if manual_inputs.bono_extraordinario_monto > 0:
            label_extra = manual_inputs.bono_extraordinario_label or "Bono Extraordinario"
            benefits.append(BenefitCalculation(
                "BONO_EXTRAORDINARIO", 
                label_extra, 
                manual_inputs.bono_extraordinario_monto, 
                calculated_amount=manual_inputs.bono_extraordinario_monto
            ))

        # --- CÁLCULO DEDUCCIONES ---
        
        # 1. Anticipos
        for ant in manual_inputs.anticipos:
            if ant['amount'] > 0:
                deductions.append(BenefitCalculation("ANTICIPO", ant['label'], Decimal(str(ant['amount'])), calculated_amount=Decimal(str(ant['amount']))))
        
        # 2. Otras deducciones (si hubieran)
        for d in manual_inputs.deducciones:
            if d['amount'] > 0:
                deductions.append(BenefitCalculation("DEDUCCION", d['label'], Decimal(str(d['amount'])), calculated_amount=Decimal(str(d['amount']))))
        
        # 3. RC-IVA
        rc_iva = self.calculate_rc_iva(vac.calculated_amount, manual_inputs.rc_iva_flag)
        if rc_iva: deductions.append(rc_iva)
        
        # TOTALES
        total_ben = sum(b.calculated_amount for b in benefits)
        total_ded = sum(d.calculated_amount for d in deductions)
        
        return FiniquitoCalculationResult(
            calculation_id=str(uuid.uuid4()),
            employee=employee, case_params=case_params,
            antiguedad=antiguedad_real, tiempo_pago=tiempo_pago,
            payroll_months=payroll_months, salary_average=salary_avg,
            manual_inputs=manual_inputs, benefits=benefits, deductions=deductions,
            total_benefits=total_ben, total_deductions=total_ded, net_payment=total_ben - total_ded,
            calculation_date=datetime.now(), motivo_config={}
        )
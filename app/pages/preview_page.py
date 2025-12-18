"""
Preview Page - Final Corrected Version
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from decimal import Decimal
import hashlib
import json
from typing import Dict, List, Optional, Tuple, Any

from config import settings
from infra.database.connection import get_db
from infra.database.models import (
    MotivoRetiroConfig, CalculationRun, ManualInput,
    CompanyHomologation, AuditLog, CaseStatus
)
from infra.excel.excel_adapter import ExcelReader
from domain.entities import (
    Employee, PayrollMonth, ManualInputs, CaseParameters,
    FiniquitoCalculationResult, ValidationResult
)
from domain.calculator import FiniquitoCalculator
from domain.validators import FiniquitoValidator


def show_preview_page():
    st.title("📊 Vista Previa y Cálculo")
    
    if 'case_params' not in st.session_state or 'ci' not in st.session_state.case_params:
        st.error("⚠️ Por favor complete la selección de caso primero")
        return
    
    # Inicializadores
    if 'anticipos_list' not in st.session_state:
        st.session_state.anticipos_list = [{'label': '', 'amount': 0.0}]
    if 'otros_bonos_breakdown' not in st.session_state:
        st.session_state.otros_bonos_breakdown = [
            {'label': 'Bono Refrigerio', 'm1': 0.0, 'm2': 0.0, 'm3': 0.0},
            {'label': '', 'm1': 0.0, 'm2': 0.0, 'm3': 0.0}
        ]

    # Datos básicos
    ci = st.session_state.case_params['ci']
    empresa = st.session_state.case_params['empresa']
    nombre = st.session_state.case_params['nombre']
    
    # Recuperar fecha real (con fallback si el usuario no volvió a seleccionar)
    f_ingreso_real = st.session_state.case_params.get('fecha_ingreso_real')
    if not f_ingreso_real:
        # Intento de recuperación de emergencia si faltara
        f_ingreso_real = date.today() 
        st.warning("⚠️ No se detectó fecha de ingreso. Por favor vuelva a 'Selección de Caso' y seleccione al empleado nuevamente.")

    # ==========================================
    # 1. CABECERA Y DATOS SALARIALES
    # ==========================================
    st.header("1️⃣ Información Salarial")
    
    payroll_months = extract_payroll_months(ci, empresa)
    if not payroll_months:
        st.error("❌ Error al extraer datos de nómina.")
        return
    
    avg_salary = sum(m.total_ganado for m in payroll_months) / Decimal(3)
    avg_otros_bonos = sum(m.otros_bonos for m in payroll_months) / Decimal(3)
    month_names = [m.month_name for m in payroll_months]
    
    # Tarjeta de Resumen
    st.markdown(f"""
    <div style="background-color: #1E2A38; padding: 15px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-bottom: 20px;">
        <h3 style="margin:0; color: white;">{nombre}</h3>
        <p style="margin:0; color: #ccc;">CI: {ci} | Empresa: {empresa}</p>
        <hr style="border-color: #444;">
        <div style="display: flex; justify-content: space-between;">
            <div>
                <strong>Fecha Ingreso:</strong> {f_ingreso_real}<br>
                <strong>Fecha Retiro:</strong> {st.session_state.case_params['pay_until_date']}
            </div>
            <div style="text-align: right;">
                <span style="font-size: 0.9em; color: #ccc;">Promedio Indemnizable:</span><br>
                <span style="font-size: 1.5em; font-weight: bold; color: #4CAF50;">Bs. {avg_salary:,.2f}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Detalle Mensual
    st.subheader("Detalle de los últimos 3 meses")
    cols = st.columns(3)
    for idx, (col, month) in enumerate(zip(cols, payroll_months)):
        with col:
            st.markdown(f"### {month.month_name}")
            st.text(f"Haber Básico:  {month.haber_basico:,.2f}")
            st.text(f"Bono Antig.:   {month.bono_antiguedad:,.2f}")
            st.markdown(f"Otros Bonos:   **{month.otros_bonos:,.2f}**")
            st.divider()
            st.markdown(f"#### Total: {month.total_ganado:,.2f}")

    # ==========================================
    # 2. DATOS PERSONALES (RDP) - RESTAURADO
    # ==========================================
    st.header("2️⃣ Datos Personales (RDP)")
    rdp_data = extract_rdp_data(ci, empresa)
    
    if rdp_data:
        c_rdp1, c_rdp2, c_rdp3 = st.columns(3)
        with c_rdp1:
            st.text_input("CI / Documento", value=rdp_data.get('ci', ci), disabled=True)
            st.text_input("Extensión", value=rdp_data.get('extension', 'N/A'), disabled=True)
        with c_rdp2:
            st.text_input("Estado Civil", value=rdp_data.get('estado_civil', 'N/A'), disabled=True)
            st.text_input("Fecha Nacimiento", value=str(rdp_data.get('fecha_nacimiento', 'N/A')), disabled=True)
        with c_rdp3:
            st.text_area("Domicilio / Dirección", value=rdp_data.get('domicilio', 'N/A'), disabled=True, height=107)
    else:
        st.warning("⚠️ No se encontraron datos adicionales en la hoja RDP.")

    # ==========================================
    # 3. DESGLOSE DE "OTROS BONOS"
    # ==========================================
    st.header("3️⃣ Desglose de 'Otros Bonos'")
    st.caption(f"Promedio detectado en Excel: Bs. {avg_otros_bonos:,.2f}. Desglose para validar.")

    c_lbl, c_m1, c_m2, c_m3, c_avg, c_del = st.columns([2.5, 1.2, 1.2, 1.2, 1.2, 0.5])
    c_lbl.markdown("**Concepto**")
    c_m1.markdown(f"**{month_names[0]}**")
    c_m2.markdown(f"**{month_names[1]}**")
    c_m3.markdown(f"**{month_names[2]}**")
    c_avg.markdown("**Promedio**")

    total_manual_avg = Decimal(0)
    for i, item in enumerate(st.session_state.otros_bonos_breakdown):
        c_lbl, c_m1, c_m2, c_m3, c_avg, c_del = st.columns([2.5, 1.2, 1.2, 1.2, 1.2, 0.5])
        with c_lbl: item['label'] = st.text_input("", value=item['label'], key=f"ob_lbl_{i}", label_visibility="collapsed")
        with c_m1: item['m1'] = st.number_input("", value=float(item['m1']), min_value=0.0, step=10.0, key=f"ob_m1_{i}", label_visibility="collapsed")
        with c_m2: item['m2'] = st.number_input("", value=float(item['m2']), min_value=0.0, step=10.0, key=f"ob_m2_{i}", label_visibility="collapsed")
        with c_m3: item['m3'] = st.number_input("", value=float(item['m3']), min_value=0.0, step=10.0, key=f"ob_m3_{i}", label_visibility="collapsed")
        
        row_avg = (Decimal(str(item['m1'])) + Decimal(str(item['m2'])) + Decimal(str(item['m3']))) / Decimal(3)
        total_manual_avg += row_avg
        with c_avg: st.markdown(f"<div style='text-align: right; padding-top: 5px;'><b>{row_avg:,.2f}</b></div>", unsafe_allow_html=True)
        with c_del:
            if st.button("❌", key=f"del_ob_{i}"):
                st.session_state.otros_bonos_breakdown.pop(i)
                st.rerun()

    if st.button("➕ Añadir Concepto Variable"):
        st.session_state.otros_bonos_breakdown.append({'label': '', 'm1': 0.0, 'm2': 0.0, 'm3': 0.0})
        st.rerun()

    if abs(total_manual_avg - avg_otros_bonos) < 1.0:
        st.success(f"✅ VALIDADO: {total_manual_avg:,.2f} coincide con planilla")
    else:
        st.warning(f"⚠️ DIFERENCIA: Manual {total_manual_avg:,.2f} vs Excel {avg_otros_bonos:,.2f}")

    # ==========================================
    # 4. BENEFICIOS
    # ==========================================
    st.header("4️⃣ Configuración de Beneficios")
    c1, c2 = st.columns(2)
    with c1:
        vacation_days = st.number_input("Saldo de Días de Vacación:", min_value=0.0, value=15.0, step=0.5)
        rc_iva_active = st.checkbox("Descontar RC-IVA (13% de Vacaciones)", value=False)
    with c2:
        aguinaldo_excluded = st.checkbox("Excluir Aguinaldo (Ya pagado)", value=st.session_state.case_params.get('aguinaldo_already_paid_exclude', False))

    # ==========================================
    # 5. BONO EXTRAORDINARIO
    # ==========================================
    st.header("5️⃣ Bono Extraordinario")
    st.info("Pago extraordinario reconocido por la empresa (se suma al líquido pagable).")
    
    col_ext1, col_ext2 = st.columns([3, 1])
    with col_ext1:
        bono_ext_label = st.text_input("Concepto / Glosa:", placeholder="Ej: Gratificación Voluntaria")
    with col_ext2:
        bono_ext_amount = st.number_input("Importe (Bs):", min_value=0.0, step=100.0)

    # ==========================================
    # 6. DEDUCCIONES
    # ==========================================
    st.header("6️⃣ Deducciones y Anticipos")
    st.caption("Ingrese anticipos o descuentos pendientes.")
    
    d_lbl, d_amt, d_del = st.columns([3, 1.5, 0.5])
    d_lbl.caption("Concepto")
    d_amt.caption("Monto (Bs)")

    for i, item in enumerate(st.session_state.anticipos_list):
        ca, cb, cc = st.columns([3, 1.5, 0.5])
        with ca:
            item['label'] = st.text_input("", value=item['label'], key=f"ant_l_{i}", 
                                        placeholder="Ej: Anticipo de Indemnización 2014 - 2015",
                                        label_visibility="collapsed")
        with cb:
            item['amount'] = st.number_input("", value=float(item['amount']), min_value=0.0, step=100.0, key=f"ant_m_{i}", label_visibility="collapsed")
        with cc:
            if st.button("🗑️", key=f"del_ant_{i}"):
                st.session_state.anticipos_list.pop(i)
                st.rerun()

    if st.button("➕ Añadir Deducción/Anticipo"):
        st.session_state.anticipos_list.append({'label': '', 'amount': 0.0})
        st.rerun()

    # ==========================================
    # 7. CÁLCULO
    # ==========================================
    st.divider()
    if st.button("🔢 Calcular Finiquito", type="primary", use_container_width=True):
        try:
            with st.spinner("Calculando..."):
                # Crear Empleado con FECHA DE INGRESO REAL (Crítico)
                employee = create_employee_object(ci, empresa, payroll_months[0], rdp_data)
                
                # Preparar inputs
                manual_inputs = ManualInputs(
                    vacation_days_balance=Decimal(str(vacation_days)),
                    rc_iva_flag=rc_iva_active,
                    bono_extraordinario_monto=Decimal(str(bono_ext_amount)), 
                    bono_extraordinario_label=bono_ext_label,
                    anticipos=st.session_state.anticipos_list,
                    otros_conceptos=[] 
                )
                
                # Params
                case_params = CaseParameters(
                    pay_until_date=st.session_state.case_params['pay_until_date'],
                    calculation_start_date=st.session_state.case_params.get('calculation_start_date', date.today()),
                    request_date=st.session_state.case_params['request_date'],
                    motivo_retiro=st.session_state.case_params['motivo_retiro'],
                    quinquenio_start_date=st.session_state.case_params.get('quinquenio_start_date_override'),
                    aguinaldo_already_paid=aguinaldo_excluded
                )
                
                # Config
                with get_db() as db:
                    m_conf = db.query(MotivoRetiroConfig).filter_by(code=case_params.motivo_retiro).first()
                    class ConfigObj: pass
                    motivo_obj = ConfigObj()
                    if m_conf:
                        motivo_obj.dia_menos_flag = m_conf.dia_menos_flag
                        motivo_obj.indemnizacion_flag = m_conf.indemnizacion_flag
                        motivo_obj.aguinaldo_flag = m_conf.aguinaldo_flag
                        motivo_obj.desahucio_flag = m_conf.desahucio_flag
                        motivo_obj.vacaciones_flag = m_conf.vacaciones_flag
                    else:
                        motivo_obj.indemnizacion_flag = True
                        motivo_obj.aguinaldo_flag = True
                        motivo_obj.vacaciones_flag = True
                        motivo_obj.desahucio_flag = False
                        motivo_obj.dia_menos_flag = False

                # Calcular
                calculator = FiniquitoCalculator()
                result = calculator.calculate(employee, payroll_months, case_params, manual_inputs, motivo_obj)
                
                st.session_state.calculation_result = result
                st.session_state.calculation_data = {'employee': employee.__dict__, 'result_net': float(result.net_payment)}
                
                show_calculation_results(result)
                store_calculation_run(result)
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            import traceback
            st.error(traceback.format_exc())

    st.divider()
    col1, col3 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Volver"):
            st.session_state.current_page = 'case_selection'
            st.rerun()
    with col3:
        if 'calculation_result' in st.session_state:
            if st.button("Generar Documentos ➡️", type="primary"):
                st.session_state.current_page = 'generate'
                st.rerun()

# --- FUNCIONES AUXILIARES ---

def create_employee_object(ci, empresa, month, rdp):
    # Recuperamos la fecha real guardada en la selección de caso
    fecha_ingreso_real = st.session_state.case_params.get('fecha_ingreso_real')
    
    # Si sigue sin existir, intentamos sacarla del mes si es posible, o error
    if not fecha_ingreso_real:
        fecha_ingreso_real = date.today()

    return Employee(
        ci=ci, 
        name=st.session_state.case_params.get('nombre', 'Empleado'), 
        empresa=empresa, 
        unidad="U", 
        ocupacion="O", 
        fecha_ingreso=fecha_ingreso_real, 
        fecha_nacimiento=date.today()
    )

def extract_payroll_months(ci, empresa):
    payroll_months = []
    try:
        payroll_mapping = st.session_state.mappings['payroll']
        for idx, df in enumerate([st.session_state.mes1_df, st.session_state.mes2_df, st.session_state.mes3_df]):
            ci_col = payroll_mapping.get('ci')
            def norm(s): return str(s).strip().upper()
            mask = (df[ci_col].astype(str).str.strip().str.upper() == norm(ci))
            rows = df[mask]
            if rows.empty: return []
            row = rows.iloc[0]
            
            hb = row[payroll_mapping.get('haber_basico')]
            ba = row[payroll_mapping.get('bono_antiguedad')]
            tg = row[payroll_mapping.get('total_ganado')]
            
            ob = 0
            if st.session_state.mappings.get('otros_bonos'):
                col_ob = st.session_state.mappings['otros_bonos']
                if col_ob in row: ob = row[col_ob]
            if pd.isna(ob): ob = 0
            
            m_names = ["MES 1 (Antiguo)", "MES 2 (Medio)", "MES 3 (Reciente)"]
            payroll_months.append(PayrollMonth(
                month_name=m_names[idx], year_month="", 
                haber_basico=Decimal(str(hb)), bono_antiguedad=Decimal(str(ba)), 
                otros_bonos=Decimal(str(ob)), total_ganado=Decimal(str(tg))
            ))
        return payroll_months
    except: return []

def extract_rdp_data(ci, empresa):
    try:
        rdp_map = st.session_state.mappings['rdp']
        df = st.session_state.rdp_df
        ci_col = rdp_map.get('ci')
        def norm(s): return str(s).strip().upper()
        mask = (df[ci_col].astype(str).str.strip().str.upper() == norm(ci))
        rows = df[mask]
        if rows.empty: return None
        row = rows.iloc[0]
        # Recuperamos todos los datos disponibles mapeados
        return {k: row[v] for k,v in rdp_map.items() if v in row}
    except: return None

def run_validations(emp, months, params):
    # Aquí puedes reactivar tus validadores reales si lo deseas
    return True, []

def show_validation_results(res): pass

def show_calculation_results(result: FiniquitoCalculationResult):
    st.divider()
    st.header("📈 Resultados")
    c1, c2 = st.columns(2)
    with c1: st.info(f"**Antigüedad Real:** {result.antiguedad.formatted}")
    with c2: st.success(f"**Tiempo Computable:** {result.tiempo_pago.formatted}")
    
    st.subheader("Beneficios Sociales")
    data_ben = [{"Concepto": b.description, "Monto (Bs)": f"{b.calculated_amount:,.2f}"} for b in result.benefits]
    st.table(pd.DataFrame(data_ben))
    
    if result.deductions:
        st.subheader("Deducciones")
        data_ded = [{"Concepto": d.description, "Monto (Bs)": f"{d.calculated_amount:,.2f}"} for d in result.deductions]
        st.table(pd.DataFrame(data_ded))
        
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Beneficios", f"{result.total_benefits:,.2f}")
    c2.metric("Total Deducciones", f"{result.total_deductions:,.2f}")
    c3.metric("LÍQUIDO PAGABLE", f"{result.net_payment:,.2f}", delta="A PAGAR")

def store_calculation_run(result):
    try:
        with get_db() as db:
            run = CalculationRun(
                employee_ci=result.employee.ci,
                employee_name=result.employee.name,
                employee_empresa=result.employee.empresa,
                pay_until_date=result.case_params.pay_until_date,
                request_date=result.case_params.request_date,
                motivo_retiro=result.case_params.motivo_retiro,
                quinquenio_start_date=result.case_params.quinquenio_start_date,
                aguinaldo_excluded=result.case_params.aguinaldo_already_paid,
                total_benefits=float(result.total_benefits),
                total_deductions=float(result.total_deductions),
                net_payment=float(result.net_payment),
                calculation_data=json.dumps(st.session_state.calculation_data, default=str),
                input_files_hash="hash",
                status=CaseStatus.CALCULATED,
                created_by=st.session_state.get('user_id'),
                observaciones=st.session_state.case_params.get('observaciones', '')
            )
            db.add(run)
            db.commit()
            st.session_state.calculation_run_id = run.id
            st.success(f"✅ Guardado ID: {run.id}")
    except: pass
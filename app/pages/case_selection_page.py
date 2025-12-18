"""
Case Selection Page - Employee selection and case parameters (Fixed Date Capture)
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import Optional
from config import BolivianLaborConstants
from infra.database.connection import get_db
from infra.database.models import MotivoRetiroConfig, CompanyHomologation
from infra.excel.excel_adapter import ExcelReader
from domain.validators import FiniquitoValidator


def show_case_selection_page():
    st.title("👤 Selección de Caso")
    
    # Validar prerrequisitos
    if not validate_prerequisites():
        st.error("⚠️ Por favor complete el mapeo de columnas primero")
        return
    
    # Inicializar parámetros
    if 'case_params' not in st.session_state:
        st.session_state.case_params = {}
    
    st.header("1️⃣ Selección de Empleado")
    
    # Obtener datos de MES 3 (Base principal)
    payroll_mapping = st.session_state.mappings['payroll']
    mes3_df = st.session_state.mes3_df
    
    # Columnas mapeadas
    ci_col = payroll_mapping.get('ci')
    nombre_col = payroll_mapping.get('nombre')
    empresa_col = payroll_mapping.get('empresa')
    
    # Crear dataframe para el buscador (solo columnas necesarias)
    employees_df = mes3_df[[ci_col, nombre_col, empresa_col]].copy()
    employees_df.columns = ['ci', 'nombre', 'empresa']
    
    # Crear columna de visualización
    employees_df['Display'] = employees_df.apply(
        lambda x: f"{x['nombre']} | CI: {x['ci']} | {x['empresa']}", axis=1
    )
    
    # --- BUSCADOR ---
    search_term = st.text_input("🔍 Buscar empleado:", placeholder="Escribe nombre o CI...")
    
    # Filtrado
    if search_term:
        search_term = search_term.lower()
        mask = (
            employees_df['nombre'].astype(str).str.lower().str.contains(search_term) |
            employees_df['ci'].astype(str).str.lower().str.contains(search_term)
        )
        filtered_df = employees_df[mask]
    else:
        filtered_df = employees_df
    
    # Selector
    selected_employee = None
    if filtered_df.empty:
        st.warning("No se encontraron resultados.")
    else:
        # Añadimos opción vacía al principio para obligar a seleccionar
        options = ["-- Seleccionar --"] + filtered_df['Display'].tolist()
        selection = st.selectbox("Seleccionar de la lista filtrada:", options, key="sel_emp_widget")
        
        if selection != "-- Seleccionar --":
            selected_employee = selection

    # --- PROCESAR SELECCIÓN ---
    if selected_employee:
        # 1. Obtener datos básicos del selector
        row_subset = filtered_df[filtered_df['Display'] == selected_employee].iloc[0]
        selected_ci = row_subset['ci']
        selected_empresa = row_subset['empresa']
        
        # 2. Guardar en memoria
        st.session_state.case_params['ci'] = selected_ci
        st.session_state.case_params['empresa'] = selected_empresa
        st.session_state.case_params['nombre'] = row_subset['nombre']
        
        # 3. RECUPERAR FECHA INGRESO REAL (CRÍTICO - FIX)
        # Buscamos en el DataFrame ORIGINAL (mes3_df) usando el índice o match, 
        # porque 'employees_df' no tiene la columna de fecha.
        try:
            # Encontrar la fila original
            # Usamos normalización para asegurar match
            def norm(s): return str(s).strip().upper()
            
            mask_orig = (mes3_df[ci_col].astype(str).apply(norm) == norm(selected_ci)) & \
                        (mes3_df[empresa_col].astype(str).apply(norm) == norm(selected_empresa))
            
            original_row = mes3_df[mask_orig]
            
            if not original_row.empty:
                # Extraer fecha usando el mapeo
                col_fecha = payroll_mapping.get('fecha_ingreso')
                raw_fecha = original_row.iloc[0][col_fecha]
                
                # Convertir a objeto date
                fecha_real = pd.to_datetime(raw_fecha).date()
                st.session_state.case_params['fecha_ingreso_real'] = fecha_real
            else:
                st.error("Error técnico: No se encontró la fila original para recuperar la fecha.")
                
        except Exception as e:
            st.error(f"Error recuperando fecha ingreso: {e}")
            st.session_state.case_params['fecha_ingreso_real'] = date.today() # Fallback

        # --- MOSTRAR DETALLES ---
        # Validaciones visuales (Semáforo)
        c1, c2, c3, c4 = st.columns(4)
        with c1: check_mes(st.session_state.mes1_df, selected_ci, selected_empresa, "MES 1")
        with c2: check_mes(st.session_state.mes2_df, selected_ci, selected_empresa, "MES 2")
        with c3: check_mes(st.session_state.mes3_df, selected_ci, selected_empresa, "MES 3")
        with c4: check_rdp(st.session_state.rdp_df, selected_ci, selected_empresa)
        
        st.subheader("Detalles del empleado")
        show_employee_details(selected_ci, selected_empresa)
        
        # --- PARÁMETROS DEL CASO ---
        st.header("2️⃣ Parámetros del Caso")
        col1, col2 = st.columns(2)
        
        with col1:
            pay_until = st.date_input("Fecha de Retiro (último día):", value=date.today())
            st.session_state.case_params['pay_until_date'] = pay_until
            
            # Fecha Inicio Cálculo (Por defecto = Fecha Ingreso Real)
            default_start = st.session_state.case_params.get('fecha_ingreso_real', date.today())
            calc_start = st.date_input("Fecha Inicio Cálculo:", value=default_start, help="Puede ser distinta a fecha ingreso si hubo quinquenios pagados.")
            st.session_state.case_params['calculation_start_date'] = calc_start
            
            req_date = st.date_input("Fecha Solicitud:", value=date.today())
            st.session_state.case_params['request_date'] = req_date

        with col2:
            # Motivos
            with get_db() as db:
                motivos = db.query(MotivoRetiroConfig).filter_by(is_active=True).all()
                mot_dict = {m.code: m.description for m in motivos}
                sel_mot = st.selectbox("Motivo de Retiro:", list(mot_dict.keys()), format_func=lambda x: f"{x} - {mot_dict[x]}")
                st.session_state.case_params['motivo_retiro'] = sel_mot
            
            if sel_mot == "QUINQUENIO":
                q_date = st.date_input("Inicio Quinquenio (Override):")
                st.session_state.case_params['quinquenio_start_date_override'] = q_date
            
            st.text_area("Observaciones:", key="obs_input")
            st.session_state.case_params['observaciones'] = st.session_state.obs_input

        # Navegación
        st.divider()
        c_back, c_next = st.columns([1, 1])
        with c_back:
            if st.button("⬅️ Volver"):
                st.session_state.current_page = 'mapping'
                st.rerun()
        with c_next:
            if st.button("Continuar a Vista Previa ➡️", type="primary"):
                st.session_state.current_page = 'preview'
                st.rerun()

# --- FUNCIONES AUXILIARES ---
def validate_prerequisites():
    return 'mes3_df' in st.session_state and 'mappings' in st.session_state

def check_mes(df, ci, emp, label):
    # Lógica simplificada de chequeo visual
    exists = False
    try:
        mapping = st.session_state.mappings['payroll']
        # Buscar normalizado
        mask = (df[mapping['ci']].astype(str).str.strip() == str(ci).strip())
        exists = not df[mask].empty
    except: pass
    
    if exists: st.success(f"✅ {label}")
    else: st.error(f"❌ {label}")

def check_rdp(df, ci, emp):
    exists = False
    try:
        mapping = st.session_state.mappings['rdp']
        mask = (df[mapping['ci']].astype(str).str.strip() == str(ci).strip())
        exists = not df[mask].empty
    except: pass
    if exists: st.success(f"✅ RDP")
    else: st.error(f"❌ RDP")

def show_employee_details(ci, emp):
    # Mostrar tabla resumen del mes 3
    try:
        df = st.session_state.mes3_df
        map_p = st.session_state.mappings['payroll']
        mask = (df[map_p['ci']].astype(str).str.strip() == str(ci).strip())
        row = df[mask].iloc[0]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("CI", str(ci))
        c1.metric("Nombre", row[map_p['nombre']])
        c2.metric("Empresa", emp)
        c2.metric("Unidad", row[map_p.get('unidad', '')])
        
        # Mostrar fecha ingreso parseada
        f_ingreso = row[map_p['fecha_ingreso']]
        try: f_str = pd.to_datetime(f_ingreso).strftime('%Y-%m-%d')
        except: f_str = str(f_ingreso)
        c3.metric("Fecha Ingreso", f_str)
        c3.metric("Ocupación", row[map_p.get('ocupacion', '')])
        
        st.markdown("### Información Salarial (MES 3)")
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Haber Básico", f"{row[map_p['haber_basico']]:,.2f}")
        sc2.metric("Bono Antigüedad", f"{row[map_p['bono_antiguedad']]:,.2f}")
        
        ob = 0
        if st.session_state.mappings.get('otros_bonos'):
            col_ob = st.session_state.mappings['otros_bonos']
            if col_ob in row: ob = row[col_ob]
        sc3.metric("Otros Bonos", f"{ob:,.2f}")
        
        sc4.metric("Total Ganado", f"{row[map_p['total_ganado']]:,.2f}")
        
    except Exception as e:
        st.error(f"Detalles no disponibles: {e}")
"""
Case History Page - List and search calculation runs
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_, desc
from infra.database.connection import get_db
from infra.database.models import CalculationRun, GeneratedDocument

def show_case_history_page():
    st.title("📚 Historial de Casos")
    
    # --- FILTROS ---
    st.markdown("### 🔍 Búsqueda")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        search = st.text_input("Buscar (Nombre, CI o Empresa):", placeholder="Ej: Perez o 123456")
    with c2:
        status = st.selectbox("Estado:", ["Todos", "calculated", "generated", "paid"])
    with c3:
        days = st.selectbox("Periodo:", ["Últimos 30 días", "Últimos 90 días", "Todo el historial"])
    
    # --- QUERY ---
    with get_db() as db:
        query = db.query(CalculationRun)
        
        if search:
            query = query.filter(or_(
                CalculationRun.employee_name.ilike(f"%{search}%"),
                CalculationRun.employee_ci.ilike(f"%{search}%"),
                CalculationRun.employee_empresa.ilike(f"%{search}%")
            ))
        
        if status != "Todos":
            query = query.filter(CalculationRun.status == status)
            
        if days != "Todo el historial":
            delta = 30 if "30" in days else 90
            cutoff = datetime.now() - timedelta(days=delta)
            query = query.filter(CalculationRun.fecha_calculo >= cutoff)
            
        runs = query.order_by(desc(CalculationRun.fecha_calculo)).limit(50).all()
        
        # --- TABLA ---
        if not runs:
            st.info("No se encontraron registros.")
            return

        data = []
        for r in runs:
            data.append({
                "ID": r.id,
                "Fecha": r.fecha_calculo,
                "CI": r.employee_ci,
                "Empleado": r.employee_name,
                "Empresa": r.employee_empresa,
                "Motivo": r.motivo_retiro,
                "Líquido Pagable": float(r.net_payment),
                "Estado": r.status
            })
            
        df = pd.DataFrame(data)
        
        # Configuración visual de columnas
        st.dataframe(
            df,
            column_config={
                "Fecha": st.column_config.DatetimeColumn("Fecha Cálculo", format="DD/MM/YYYY HH:mm"),
                "Líquido Pagable": st.column_config.NumberColumn("Neto (Bs)", format="Bs %.2f"),
                "Estado": st.column_config.TextColumn("Estado", help="Estado del trámite"),
            },
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            key="history_table"
        )
        
        # --- ACCIONES SOBRE SELECCIÓN ---
        # Streamlit dataframe selection logic
        # (Alternativa simple con botones por fila si la selección nativa falla, 
        # pero aquí usaremos un selector de ID para robustez)
        
        st.divider()
        col_act1, col_act2 = st.columns([2, 1])
        with col_act1:
            selected_id = st.selectbox("Seleccionar Caso para Acciones:", [r.id for r in runs], format_func=lambda x: f"Caso #{x}")
        
        with col_act2:
            if st.button("👁️ Ver Detalle Completo", type="primary", use_container_width=True):
                st.session_state.selected_case_id = selected_id
                st.session_state.current_page = 'case_detail'
                st.rerun()
                
            if st.button("🔄 Cargar en Generador", use_container_width=True):
                st.session_state.calculation_run_id = selected_id
                st.session_state.current_page = 'generate'
                st.rerun()

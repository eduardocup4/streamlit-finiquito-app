"""
Case Detail Page - Detailed view of a calculation (Enhanced)
"""

import streamlit as st
import json
import pandas as pd
from infra.database.connection import get_db
from infra.database.models import CalculationRun, ManualInput

def show_case_detail_page():
    st.title("📋 Detalle del Caso")
    
    case_id = st.session_state.get('selected_case_id')
    if not case_id:
        st.warning("No hay caso seleccionado.")
        if st.button("Volver"):
            st.session_state.current_page = 'history'
            st.rerun()
        return

    with get_db() as db:
        case = db.query(CalculationRun).filter_by(id=case_id).first()
        if not case:
            st.error("Caso no encontrado.")
            return

        # --- HEADER ---
        st.markdown(f"""
        <div style="padding: 20px; background-color: #262730; border-radius: 10px; border: 1px solid #444;">
            <h2 style="margin:0; color: white;">{case.employee_name}</h2>
            <p style="margin:0; color: #aaa;">CI: {case.employee_ci} | Empresa: {case.employee_empresa}</p>
            <hr>
            <div style="display:flex; justify-content:space-between;">
                <div><b>Motivo:</b> {case.motivo_retiro}</div>
                <div><b>Estado:</b> {case.status.upper()}</div>
                <div><b>Fecha:</b> {case.fecha_calculo.strftime('%d/%m/%Y')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()

        # --- PARSEO DEL JSON ---
        try:
            data = json.loads(case.calculation_data)
            
            # 1. RESUMEN FINANCIERO
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Beneficios", f"Bs. {case.total_benefits:,.2f}")
            c2.metric("Total Deducciones", f"Bs. {case.total_deductions:,.2f}")
            c3.metric("LÍQUIDO PAGABLE", f"Bs. {case.net_payment:,.2f}", delta="Final")
            
            # 2. DETALLE DE BENEFICIOS (NUEVO DESGLOSE)
            st.subheader("💰 Beneficios Sociales")
            
            # Intentar sacar beneficios del JSON estructurado
            # El JSON suele tener estructura {'benefits': [{'concept':..., 'calculated_amount':...}]}
            # Adaptamos según tu estructura de entities.py serialize
            
            benefits_list = []
            raw_benefits = data.get('benefits', [])
            # Si el json guardó objetos complejos, puede variar. Asumimos lista de dicts.
            
            if isinstance(raw_benefits, list):
                for b in raw_benefits:
                    # Soporte para estructura dict o objeto serializado
                    desc = b.get('description', b.get('concept', ''))
                    amt = float(b.get('calculated_amount', b.get('amount', 0)))
                    if amt > 0:
                        benefits_list.append({"Concepto": desc, "Monto": f"{amt:,.2f}"})
            
            if benefits_list:
                st.table(pd.DataFrame(benefits_list))
            else:
                st.info("Sin detalle de beneficios disponible.")

            # 3. DEDUCCIONES Y ANTICIPOS
            st.subheader("📉 Deducciones y Anticipos")
            deductions_list = []
            raw_deductions = data.get('deductions', [])
            
            if isinstance(raw_deductions, list):
                for d in raw_deductions:
                    desc = d.get('description', d.get('concept', ''))
                    amt = float(d.get('calculated_amount', d.get('amount', 0)))
                    if amt > 0:
                        deductions_list.append({"Concepto": desc, "Monto": f"{amt:,.2f}"})
            
            if deductions_list:
                st.table(pd.DataFrame(deductions_list))
            else:
                st.text("No hay deducciones registradas.")

            # 4. DATOS ADICIONALES
            with st.expander("ℹ️ Detalles Técnicos y Observaciones"):
                st.write(f"**Creado por User ID:** {case.created_by}")
                st.write(f"**Hash Archivos:** {case.input_files_hash}")
                st.write(f"**Observaciones:** {case.observaciones}")
                
                if 'manual_inputs' in data:
                    st.json(data['manual_inputs'])

        except Exception as e:
            st.error(f"Error al leer detalles del cálculo: {e}")
            st.json(case.calculation_data) # Fallback raw view

    st.divider()
    if st.button("⬅️ Volver al Historial"):
        st.session_state.current_page = 'history'
        st.rerun()
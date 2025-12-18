"""
Admin Page - Configuration and Management
"""

import streamlit as st
import pandas as pd
from infra.database.connection import get_db, init_database
from infra.database.models import User, CompanyHomologation, MotivoRetiroConfig
from config import settings

def show_admin_page():
    st.title("⚙️ Administración")
    
    # Security Check
    if st.session_state.get('role') != 'admin': # Asumiendo gestión de roles
        st.warning("Acceso restringido a administradores.")
        # return # Descomentar en producción

    tabs = st.tabs(["🏢 Empresas", "📋 Motivos", "🔧 Base de Datos"])

    # --- TAB 1: EMPRESAS ---
    with tabs[0]:
        st.subheader("Homologación de Nombres de Empresa")
        st.info("Defina alias para unificar nombres (ej. 'Coca Cola' -> 'EMBOL S.A.')")
        
        with get_db() as db:
            # Lista
            homologs = db.query(CompanyHomologation).filter_by(is_active=True).all()
            if homologs:
                df = pd.DataFrame([{"Alias": h.alias, "Oficial": h.normalized_name} for h in homologs])
                st.dataframe(df, use_container_width=True)
            
            # Agregar
            c1, c2, c3 = st.columns([2, 2, 1])
            alias = c1.text_input("Alias (Nombre en Excel)")
            oficial = c2.text_input("Nombre Oficial")
            if c3.button("➕ Agregar"):
                if alias and oficial:
                    h = CompanyHomologation(alias=alias, normalized_name=oficial)
                    db.add(h)
                    db.commit()
                    st.success("Guardado")
                    st.rerun()

    # --- TAB 2: MOTIVOS ---
    with tabs[1]:
        st.subheader("Configuración de Motivos de Retiro")
        with get_db() as db:
            motivos = db.query(MotivoRetiroConfig).all()
            
            # Editor tipo Grid
            for m in motivos:
                with st.expander(f"⚙️ {m.description} ({m.code})"):
                    c1, c2, c3 = st.columns(3)
                    new_indem = c1.checkbox("Paga Indemnización", value=m.indemnizacion_flag, key=f"i_{m.id}")
                    new_desah = c2.checkbox("Paga Desahucio", value=m.desahucio_flag, key=f"d_{m.id}")
                    new_vac = c3.checkbox("Paga Vacaciones", value=m.vacaciones_flag, key=f"v_{m.id}")
                    
                    if st.button("Guardar Cambios", key=f"btn_{m.id}"):
                        m.indemnizacion_flag = new_indem
                        m.desahucio_flag = new_desah
                        m.vacaciones_flag = new_vac
                        db.commit()
                        st.success("Actualizado")

    # --- TAB 3: DATABASE ---
    with tabs[2]:
        st.subheader("Mantenimiento")
        st.warning("⚠️ Zona de Peligro")
        
        if st.button("🔥 REINICIALIZAR BASE DE DATOS (BORRA TODO)"):
            init_database()
            st.success("Base de datos reiniciada a cero.")
            st.rerun()

    st.divider()
    if st.button("⬅️ Volver"):
        st.session_state.current_page = 'history'
        st.rerun()
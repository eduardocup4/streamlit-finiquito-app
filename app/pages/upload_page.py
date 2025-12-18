"""
Upload page for Excel files
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import shutil
from datetime import datetime
import hashlib

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from config import settings, UPLOADS_DIR

def save_uploaded_file(uploaded_file, prefix=""):
    """Save uploaded file to storage"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{prefix}_{timestamp}_{uploaded_file.name}"
    file_path = UPLOADS_DIR / file_name
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def show():
    """Show upload page"""
    st.markdown("## 📤 Carga de Archivos")
    
    st.info("""
    **Archivos requeridos:**
    1. **3 archivos de nómina** (últimos 3 meses completos)
    2. **1 archivo RDP** (base de datos personal)
    
    Todos los archivos deben ser en formato Excel (.xlsx o .xls)
    """)
    
    # Create columns for file uploads
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Archivos de Nómina")
        
        # Month 1 (oldest)
        st.markdown("#### Mes 1 (más antiguo)")
        payroll_1 = st.file_uploader(
            "Seleccione archivo de nómina del Mes 1",
            type=['xlsx', 'xls'],
            key="payroll_1",
            help="Este debe ser el mes más antiguo de los 3"
        )
        
        # Month 2
        st.markdown("#### Mes 2")
        payroll_2 = st.file_uploader(
            "Seleccione archivo de nómina del Mes 2",
            type=['xlsx', 'xls'],
            key="payroll_2",
            help="Este es el mes intermedio"
        )
        
        # Month 3 (most recent)
        st.markdown("#### Mes 3 (más reciente)")
        payroll_3 = st.file_uploader(
            "Seleccione archivo de nómina del Mes 3",
            type=['xlsx', 'xls'],
            key="payroll_3",
            help="Este debe ser el mes más reciente"
        )
    
    with col2:
        st.markdown("### 👥 Archivo RDP")
        st.markdown("#### Base de Datos Personal")
        rdp_file = st.file_uploader(
            "Seleccione archivo RDP",
            type=['xlsx', 'xls'],
            key="rdp_file",
            help="Archivo con datos personales de empleados (CI, domicilio, estado civil, etc.)"
        )
        
        # File validation info
        st.markdown("### ✅ Validaciones")
        
        validations = []
        
        # Check if all files are uploaded
        if payroll_1:
            validations.append("✅ Mes 1 cargado")
        else:
            validations.append("❌ Mes 1 pendiente")
        
        if payroll_2:
            validations.append("✅ Mes 2 cargado")
        else:
            validations.append("❌ Mes 2 pendiente")
        
        if payroll_3:
            validations.append("✅ Mes 3 cargado")
        else:
            validations.append("❌ Mes 3 pendiente")
        
        if rdp_file:
            validations.append("✅ RDP cargado")
        else:
            validations.append("❌ RDP pendiente")
        
        for validation in validations:
            st.markdown(validation)
    
    # Process button
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 Procesar Archivos", use_container_width=True, type="primary"):
            if all([payroll_1, payroll_2, payroll_3, rdp_file]):
                with st.spinner("Guardando archivos..."):
                    try:
                        # Save files
                        st.session_state.payroll_file1_path = save_uploaded_file(payroll_1, "payroll_mes1")
                        st.session_state.payroll_file2_path = save_uploaded_file(payroll_2, "payroll_mes2")
                        st.session_state.payroll_file3_path = save_uploaded_file(payroll_3, "payroll_mes3")
                        st.session_state.rdp_file_path = save_uploaded_file(rdp_file, "rdp")
                                                                   
                        # Calculate hash for tracking
                        file_contents = []
                        for file in [payroll_1, payroll_2, payroll_3, rdp_file]:
                            file_contents.append(file.getvalue())
                        
                        combined_hash = hashlib.sha256(b''.join(file_contents)).hexdigest()
                        st.session_state.files_hash = combined_hash
                        
                        st.success("✅ Archivos cargados exitosamente")
                        
                        # Auto-navigate to mapping page
                        st.session_state.current_page = "mapping"
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error al procesar archivos: {str(e)}")
            else:
                st.error("Por favor cargue todos los archivos requeridos")
    
    # Show preview if files are uploaded
    if any([payroll_1, payroll_2, payroll_3, rdp_file]):
        st.markdown("---")
        st.markdown("### 👀 Vista Previa de Archivos")
        
        tabs = []
        if payroll_1:
            tabs.append("Mes 1")
        if payroll_2:
            tabs.append("Mes 2")
        if payroll_3:
            tabs.append("Mes 3")
        if rdp_file:
            tabs.append("RDP")
        
        if tabs:
            tab_objects = st.tabs(tabs)
            tab_index = 0
            
            if payroll_1:
                with tab_objects[tab_index]:
                    try:
                        df = pd.read_excel(payroll_1)
                        st.markdown(f"**Registros:** {len(df)}")
                        st.markdown(f"**Columnas:** {', '.join(df.columns[:10])}")
                        if len(df.columns) > 10:
                            st.markdown(f"... y {len(df.columns) - 10} más")
                        st.dataframe(df.head(), use_container_width=True)
                    except Exception as e:
                        st.error(f"Error al leer archivo: {str(e)}")
                tab_index += 1
            
            if payroll_2:
                with tab_objects[tab_index]:
                    try:
                        df = pd.read_excel(payroll_2)
                        st.markdown(f"**Registros:** {len(df)}")
                        st.markdown(f"**Columnas:** {', '.join(df.columns[:10])}")
                        if len(df.columns) > 10:
                            st.markdown(f"... y {len(df.columns) - 10} más")
                        st.dataframe(df.head(), use_container_width=True)
                    except Exception as e:
                        st.error(f"Error al leer archivo: {str(e)}")
                tab_index += 1
            
            if payroll_3:
                with tab_objects[tab_index]:
                    try:
                        df = pd.read_excel(payroll_3)
                        st.markdown(f"**Registros:** {len(df)}")
                        st.markdown(f"**Columnas:** {', '.join(df.columns[:10])}")
                        if len(df.columns) > 10:
                            st.markdown(f"... y {len(df.columns) - 10} más")
                        st.dataframe(df.head(), use_container_width=True)
                    except Exception as e:
                        st.error(f"Error al leer archivo: {str(e)}")
                tab_index += 1
            
            if rdp_file:
                with tab_objects[tab_index]:
                    try:
                        df = pd.read_excel(rdp_file)
                        st.markdown(f"**Registros:** {len(df)}")
                        st.markdown(f"**Columnas:** {', '.join(df.columns[:10])}")
                        if len(df.columns) > 10:
                            st.markdown(f"... y {len(df.columns) - 10} más")
                        st.dataframe(df.head(), use_container_width=True)
                    except Exception as e:
                        st.error(f"Error al leer archivo: {str(e)}")

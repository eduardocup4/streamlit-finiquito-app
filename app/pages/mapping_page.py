"""
Mapping Page - Column mapping and sheet selection for uploaded files
"""

import streamlit as st
import pandas as pd
import json
from typing import Dict, List, Optional
from pathlib import Path
from config import FieldMappingConfig
from infra.database.connection import get_db
from infra.database.models import MappingProfile
from infra.excel.excel_adapter import ExcelReader
from domain.validators import FiniquitoValidator


def show_mapping_page():
    st.title("📋 Mapeo de Columnas")
    
    if not all(key in st.session_state for key in ['payroll_file1_path', 'payroll_file2_path', 
                                                    'payroll_file3_path', 'rdp_file_path']):
        st.error("⚠️ Por favor, primero sube los archivos en la página de Upload")
        return
    
    excel_reader = ExcelReader()
    
    # Initialize mapping state
    if 'mappings' not in st.session_state:
        st.session_state.mappings = {}
    
    # Sheet selection section
    st.header("1️⃣ Selección de Hojas")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Archivos de Nómina")
        
        # MES 1
        mes1_sheets = excel_reader.get_sheet_names(st.session_state.payroll_file1_path)
        mes1_sheet = st.selectbox(
            "Hoja para MES 1 (más antiguo)",
            mes1_sheets,
            key="mes1_sheet"
        )
        
        # MES 2
        mes2_sheets = excel_reader.get_sheet_names(st.session_state.payroll_file2_path)
        mes2_sheet = st.selectbox(
            "Hoja para MES 2",
            mes2_sheets,
            key="mes2_sheet"
        )
        
        # MES 3
        mes3_sheets = excel_reader.get_sheet_names(st.session_state.payroll_file3_path)
        mes3_sheet = st.selectbox(
            "Hoja para MES 3 (más reciente)",
            mes3_sheets,
            key="mes3_sheet"
        )
    
    with col2:
        st.subheader("Base de Datos RDP")
        rdp_sheets = excel_reader.get_sheet_names(st.session_state.rdp_file_path)
        rdp_sheet = st.selectbox(
            "Hoja para RDP",
            rdp_sheets,
            key="rdp_sheet"
        )
    
    # Load data with selected sheets
    if st.button("Cargar datos con hojas seleccionadas"):
        try:
            with st.spinner("Cargando datos de los archivos..."):
                # Load each file with selected sheet
                mes1_df = excel_reader.read_excel_file(
                    st.session_state.payroll_file1_path, mes1_sheet
                )
                mes2_df = excel_reader.read_excel_file(
                    st.session_state.payroll_file2_path, mes2_sheet
                )
                mes3_df = excel_reader.read_excel_file(
                    st.session_state.payroll_file3_path, mes3_sheet
                )
                rdp_df = excel_reader.read_excel_file(
                    st.session_state.rdp_file_path, rdp_sheet
                )
                
                st.session_state.mes1_df = mes1_df
                st.session_state.mes2_df = mes2_df
                st.session_state.mes3_df = mes3_df
                st.session_state.rdp_df = rdp_df
                
                st.success("✅ Datos cargados correctamente")
        except Exception as e:
            st.error(f"❌ Error al cargar datos: {str(e)}")
            return
    
    # Column mapping section
    if all(key in st.session_state for key in ['mes1_df', 'mes2_df', 'mes3_df', 'rdp_df']):
        st.header("2️⃣ Mapeo de Columnas")
        
        # Load or create mapping profile
        col1, col2 = st.columns([2, 1])
        with col1:
            with get_db() as db:
                profiles = db.query(MappingProfile).all()
                profile_options = ["Crear nuevo perfil"] + [p.profile_name for p in profiles]
                
                selected_profile = st.selectbox(
                    "Seleccionar perfil de mapeo",
                    profile_options
                )
        
        with col2:
            if selected_profile != "Crear nuevo perfil":
                if st.button("Cargar perfil"):
                    with get_db() as db:
                        profile = db.query(MappingProfile).filter_by(
                            profile_name=selected_profile
                        ).first()
                        if profile:
                            st.session_state.mappings = json.loads(profile.mapping_data)
                            st.success(f"✅ Perfil '{selected_profile}' cargado")
        
        # Get available columns
        payroll_columns = list(st.session_state.mes3_df.columns)
        rdp_columns = list(st.session_state.rdp_df.columns)
        
        # Auto-detect mappings
        if st.button("🔍 Auto-detectar mapeos"):
            
            # 1. Definir Diccionario de Alias
            PAYROLL_ALIASES = {
                'nombre': ['Nombre', 'Nombres', 'Apellidos y Nombres', 'Empleado', 'Trabajador'],
                'ci': ['CI', 'C.I.', 'Carnet', 'Documento', 'Doc. Identidad', 'Nro. Doc'],
                'ocupacion': ['Ocupacion', 'Ocupación', 'Cargo', 'Ocup. que Desempeña', 'Puesto'],
                'fecha_nacimiento': ['Fecha Nacimiento', 'Fecha_Nacimiento', 'Nacimiento', 'F. Nac'],
                'fecha_ingreso': ['Fecha Ingreso', 'Fecha_Ingreso', 'Ingreso', 'F. Ingreso'],
                'haber_basico': ['Haber Basico', 'Haber Básico', 'Sueldo Basico', 'Básico'],
                'bono_antiguedad': ['Bono Antiguedad', 'Bono Antigüedad', 'Antiguedad'],
                'total_ganado': ['Total Ganado', 'Total General', 'Liquido Pagable'],
                'empresa': ['Empresa', 'Razon Social', 'Entidad'],
                'unidad': ['Unidad', 'Unidad de Negocio', 'Sucursal', 'Agencia']
            }

            RDP_ALIASES = {
                'empresa': ['Empresa', 'Razon Social'],
                'ci': ['Nro. Doc', 'CI', 'C.I.', 'Documento'],
                'extension': ['Extension', 'Extensión', 'Ext', 'Lugar'],
                'estado_civil': ['Estado Civil', 'E. Civil'],
                'domicilio': ['Dirección', 'Direccion', 'Domicilio', 'Vivienda']
            }

            # 2. Función auxiliar
            def find_best_match(columns, required_fields, aliases_dict):
                mapping = {}
                norm_columns = {col.lower().strip(): col for col in columns}
                
                for field in required_fields:
                    match_found = None
                    if field in aliases_dict:
                        for alias in aliases_dict[field]:
                            clean_alias = alias.lower().strip()
                            if clean_alias in norm_columns:
                                match_found = norm_columns[clean_alias]
                                break
                    
                    if not match_found:
                        clean_field = field.lower().strip()
                        if clean_field in norm_columns:
                            match_found = norm_columns[clean_field]
                    
                    if match_found:
                        mapping[field] = match_found
                return mapping

            # 3. Ejecutar detección
            payroll_mapping = find_best_match(
                payroll_columns, 
                FieldMappingConfig.REQUIRED_PAYROLL_FIELDS,
                PAYROLL_ALIASES
            )
            
            rdp_mapping = find_best_match(
                rdp_columns,
                FieldMappingConfig.REQUIRED_RDP_FIELDS,
                RDP_ALIASES
            )
            
            # 4. Guardar en estado
            st.session_state.mappings = {
                'payroll': payroll_mapping,
                'rdp': rdp_mapping,
                'otros_bonos': None,
                'include_otros_bonos': False
            }
            
            # 5. Feedback y Recarga (CRÍTICO)
            st.success("✅ Mapeo detectado. Actualizando interfaz...")
            st.rerun()  # <--- ESTA LÍNEA ES LA CLAVE PARA QUE LOS COMBOS SE ACTUALICEN
        
        # Manual mapping interface
        st.subheader("Mapeo de campos de Nómina")
        
        payroll_mapping = st.session_state.mappings.get('payroll', {})
        
        col1, col2 = st.columns(2)
        for idx, field in enumerate(FieldMappingConfig.REQUIRED_PAYROLL_FIELDS):
            with col1 if idx % 2 == 0 else col2:
                current_value = payroll_mapping.get(field, None)
                selected = st.selectbox(
                    f"{field}:",
                    ["-- Seleccionar --"] + payroll_columns,
                    index=0 if current_value is None else payroll_columns.index(current_value) + 1,
                    key=f"payroll_{field}"
                )
                if selected != "-- Seleccionar --":
                    if 'payroll' not in st.session_state.mappings:
                        st.session_state.mappings['payroll'] = {}
                    st.session_state.mappings['payroll'][field] = selected
        
        # Otros Bonos mapping (optional)
        st.subheader("Campo Opcional: Otros Bonos")
        col1, col2 = st.columns(2)
        
        with col1:
            otros_bonos_column = st.selectbox(
                "Columna de Otros Bonos (opcional):",
                ["-- No mapear --"] + payroll_columns,
                key="otros_bonos_column"
            )
            if otros_bonos_column != "-- No mapear --":
                st.session_state.mappings['otros_bonos'] = otros_bonos_column
        
        with col2:
            include_in_validation = st.checkbox(
                "Incluir Otros Bonos en validación de TotalGanado",
                value=st.session_state.mappings.get('include_otros_bonos', False),
                key="include_otros_bonos"
            )
            st.session_state.mappings['include_otros_bonos'] = include_in_validation
        
        st.subheader("Mapeo de campos RDP")
        
        rdp_mapping = st.session_state.mappings.get('rdp', {})
        
        col1, col2 = st.columns(2)
        for idx, field in enumerate(FieldMappingConfig.REQUIRED_RDP_FIELDS):
            with col1 if idx % 2 == 0 else col2:
                current_value = rdp_mapping.get(field, None)
                selected = st.selectbox(
                    f"{field}:",
                    ["-- Seleccionar --"] + rdp_columns,
                    index=0 if current_value is None else rdp_columns.index(current_value) + 1,
                    key=f"rdp_{field}"
                )
                if selected != "-- Seleccionar --":
                    if 'rdp' not in st.session_state.mappings:
                        st.session_state.mappings['rdp'] = {}
                    st.session_state.mappings['rdp'][field] = selected
        
        # Save mapping profile
        st.subheader("Guardar perfil de mapeo")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            profile_name = st.text_input("Nombre del perfil:", key="new_profile_name")
        
        with col2:
            if st.button("💾 Guardar perfil"):
                if profile_name:
                    try:
                        with get_db() as db:
                            # Check if profile exists
                            existing = db.query(MappingProfile).filter_by(
                                profile_name=profile_name
                            ).first()
                            
                            if existing:
                                existing.mapping_data = json.dumps(st.session_state.mappings)
                            else:
                                new_profile = MappingProfile(
                                    profile_name=profile_name,
                                    mapping_data=json.dumps(st.session_state.mappings),
                                    is_active=True
                                )
                                db.add(new_profile)
                            
                            db.commit()
                            st.success(f"✅ Perfil '{profile_name}' guardado")
                    except Exception as e:
                        st.error(f"❌ Error al guardar perfil: {str(e)}")
                else:
                    st.warning("⚠️ Ingrese un nombre para el perfil")
        
        # Preview mapped data
        st.header("3️⃣ Vista previa de datos mapeados")
        
        if st.button("Ver vista previa (5 filas aleatorias)"):
            if validate_mappings():
                show_preview_data()
            else:
                st.error("⚠️ Por favor complete todos los mapeos requeridos")
        
        # Navigation buttons
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("⬅️ Volver a Upload"):
                st.session_state.current_page = 'upload'
                st.rerun()
        
        with col3:
            if st.button("Continuar a Selección de Caso ➡️", type="primary"):
                if validate_mappings():
                    st.session_state.current_page = 'case_selection'
                    st.rerun()
                else:
                    st.error("⚠️ Por favor complete todos los mapeos requeridos")


def validate_mappings() -> bool:
    """Validate that all required mappings are complete"""
    if 'mappings' not in st.session_state:
        return False
    
    mappings = st.session_state.mappings
    
    # Check payroll mappings
    if 'payroll' not in mappings:
        return False
    
    for field in FieldMappingConfig.REQUIRED_PAYROLL_FIELDS:
        if field not in mappings['payroll'] or mappings['payroll'][field] is None:
            return False
    
    # Check RDP mappings
    if 'rdp' not in mappings:
        return False
    
    for field in FieldMappingConfig.REQUIRED_RDP_FIELDS:
        if field not in mappings['rdp'] or mappings['rdp'][field] is None:
            return False
    
    return True


def show_preview_data():
    """Show preview of mapped data"""
    try:
        # Sample 5 random rows from MES3
        sample_df = st.session_state.mes3_df.sample(min(5, len(st.session_state.mes3_df)))
        
        # Get mapped columns
        payroll_mapping = st.session_state.mappings['payroll']
        mapped_columns = list(payroll_mapping.values())
        
        # Add otros bonos if mapped
        if st.session_state.mappings.get('otros_bonos'):
            mapped_columns.append(st.session_state.mappings['otros_bonos'])
        
        # Show only mapped columns
        preview_df = sample_df[mapped_columns].copy()
        
        # Rename columns to canonical names
        rename_dict = {v: k for k, v in payroll_mapping.items()}
        if st.session_state.mappings.get('otros_bonos'):
            rename_dict[st.session_state.mappings['otros_bonos']] = 'OtrosBonos'
        
        preview_df.rename(columns=rename_dict, inplace=True)
        
        st.dataframe(preview_df, use_container_width=True)
        
        # Validate totals if required
        if st.session_state.mappings.get('include_otros_bonos'):
            st.info("ℹ️ Validación de TotalGanado incluirá Otros Bonos")
            
            # Quick validation check
            validator = FiniquitoValidator()
            for idx, row in preview_df.iterrows():
                haber_basico = row.get('HaberBasico', 0) or 0
                bono_antiguedad = row.get('BonoAntiguedad', 0) or 0
                otros_bonos = row.get('OtrosBonos', 0) or 0
                total_ganado = row.get('TotalGanado', 0) or 0
                
                calculated = haber_basico + bono_antiguedad + otros_bonos
                diff = abs(total_ganado - calculated)
                
                if diff > 0.01:  # 1 cent tolerance
                    st.warning(f"⚠️ Diferencia en fila {idx}: {diff:.2f} Bs")
    
    except Exception as e:
        st.error(f"❌ Error al generar vista previa: {str(e)}")

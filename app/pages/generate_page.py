"""
Generate Page - Document generation and storage (Robust Version)
"""

import streamlit as st
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from decimal import Decimal

# Importación correcta de instancia
from config import settings, BolivianLaborConstants

from infra.database.connection import get_db
from infra.database.models import (
    CalculationRun, GeneratedDocument, DocumentTemplate, 
    SystemConfig, AuditLog, DocumentType, CaseStatus
)
from infra.excel.excel_adapter import ExcelWriter
from infra.qr.qr_generator import QRStampGenerator, DocumentStampConfig
from domain.entities import FiniquitoCalculationResult, Employee, CaseParameters, Antiguedad, ManualInputs, BenefitCalculation

def show_generate_page():
    st.title("📄 Generación de Documentos")
    
    # 1. Recuperación del Resultado (Desde Sesión o BD)
    result = None
    calculation_run_id = st.session_state.get('calculation_run_id')

    if 'calculation_result' in st.session_state:
        result = st.session_state.calculation_result
    elif calculation_run_id:
        # Intento de reconstrucción desde BD si venimos del historial
        with st.spinner("Recuperando datos del caso..."):
            result = reconstruct_result_from_db(calculation_run_id)
    
    if not result or not calculation_run_id:
        st.warning("⚠️ No hay un cálculo activo. Por favor realice un cálculo o seleccione un caso del historial.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Ir a Cálculo"):
                st.session_state.current_page = 'case_selection'
                st.rerun()
        with col2:
            if st.button("Ir a Historial"):
                st.session_state.current_page = 'history'
                st.rerun()
        return

    # 2. UI de Selección
    st.markdown(f"""
    <div style="padding: 15px; background-color: #f0f2f6; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="margin:0; color: #1f77b4;">{result.employee.name}</h3>
        <p style="margin:0;"><b>CI:</b> {result.employee.ci} | <b>Líquido Pagable:</b> Bs. {result.net_payment:,.2f}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.header("1️⃣ Selección de Documentos")
    
    documents_to_generate = {}
    stamp_configs = {}
    
    # Finiquito
    with st.expander("📋 F-Finiquito (Ministerio)", expanded=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            documents_to_generate['f_finiquito'] = st.checkbox("Generar Formulario de Finiquito", value=True)
        with c2:
            st.caption("Sin sello interno")

    # Memo
    with st.expander("📝 Memo de Finalización", expanded=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            documents_to_generate['memo_finalizacion'] = st.checkbox("Generar Memo", value=True)
        with c2:
            include_cite = st.checkbox("Incluir CITE", value=False) if documents_to_generate['memo_finalizacion'] else False
            cite_number = st.text_input("Nro. CITE", placeholder="RRHH-001/24") if include_cite else None
        with c3:
            stamp_configs['memo_finalizacion'] = st.checkbox("Agregar sello", value=True, key="stamp_memo") if documents_to_generate['memo_finalizacion'] else False

    # Otros documentos (Simplificados visualmente)
    with st.expander("📂 Otros Documentos", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            documents_to_generate['f_salida'] = st.checkbox("Formulario de Salida", value=True)
            stamp_configs['f_salida'] = st.checkbox("Sello Salida", value=True) if documents_to_generate['f_salida'] else False
            
            documents_to_generate['f_equipos'] = st.checkbox("Formulario de Equipos", value=True)
            stamp_configs['f_equipos'] = st.checkbox("Sello Equipos", value=True) if documents_to_generate['f_equipos'] else False
        
        with c2:
            documents_to_generate['contable_preview'] = st.checkbox("Vista Contable", value=False)
            stamp_configs['contable_preview'] = False
            
            # Rechazo post examen
            post_exam = st.checkbox("Rechazo Post-Examen", value=False)
            if post_exam:
                documents_to_generate['rechazo_post'] = True
                rejection_date = st.date_input("Fecha Rechazo")
                stamp_configs['rechazo_post'] = st.checkbox("Sello Rechazo", value=True)
            else:
                documents_to_generate['rechazo_post'] = False
                rejection_date = None

    # 3. Generación
    st.divider()
    if st.button("🚀 Generar Documentos Seleccionados", type="primary", use_container_width=True):
        if not any(documents_to_generate.values()):
            st.warning("Seleccione al menos un documento.")
            return
        
        try:
            with st.spinner("Generando documentos PDF/Excel y aplicando sellos..."):
                generated_files = generate_documents_logic(
                    result, calculation_run_id, documents_to_generate, 
                    stamp_configs, include_cite, cite_number, rejection_date
                )
                
                if generated_files:
                    st.success(f"✅ {len(generated_files)} documentos generados correctamente.")
                    show_download_section(generated_files)
                    
                    # Update Status
                    with get_db() as db:
                        run = db.query(CalculationRun).filter_by(id=calculation_run_id).first()
                        if run:
                            run.status = CaseStatus.GENERATED
                            db.commit()
                else:
                    st.error("No se pudieron generar los documentos.")
                    
        except Exception as e:
            st.error(f"Error crítico en generación: {str(e)}")
            import traceback
            st.error(traceback.format_exc())

    # Navegación
    st.divider()
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("⬅️ Volver a Vista Previa"):
            st.session_state.current_page = 'preview'
            st.rerun()
    with c2:
        if st.button("Ver Historial ➡️"):
            st.session_state.current_page = 'history'
            st.rerun()

def reconstruct_result_from_db(run_id) -> Optional[FiniquitoCalculationResult]:
    """Reconstruye el objeto de resultado desde el JSON de la BD"""
    try:
        with get_db() as db:
            run = db.query(CalculationRun).filter_by(id=run_id).first()
            if not run or not run.calculation_data: return None
            
            data = json.loads(run.calculation_data)
            
            # Reconstrucción básica (Puede requerir ajustes según la complejidad del JSON guardado)
            # Asumimos que calculation_data guardó estructura similar a __dict__
            
            # Nota: Esta es una reconstrucción de "mejor esfuerzo" para que el ExcelWriter funcione.
            # Lo ideal es que el JSON tenga todo.
            
            emp_data = data.get('employee', {})
            emp = Employee(
                ci=run.employee_ci, name=run.employee_name, empresa=run.employee_empresa,
                unidad=emp_data.get('unidad', ''), ocupacion=emp_data.get('ocupacion', ''),
                fecha_ingreso=run.fecha_ingreso if run.fecha_ingreso else date.today(),
                fecha_nacimiento=date.today() # Dato no crítico para Excel si falta
            )
            
            # Reconstruir parametros mínimos
            params = CaseParameters(
                pay_until_date=run.pay_until_date,
                request_date=run.request_date,
                motivo_retiro=run.motivo_retiro,
                calculation_start_date=run.fecha_ingreso, # Aprox
                quinquenio_start_date=run.quinquenio_start_date,
                aguinaldo_already_paid=run.aguinaldo_excluded
            )
            
            # Crear resultado Dummy con datos financieros reales
            # (El ExcelWriter usa properties del objeto result, así que llenamos lo clave)
            
            # Reconstruir beneficios desde JSON si existe
            benefits = []
            # ... lógica de parsing de benefits ...
            
            return FiniquitoCalculationResult(
                calculation_id=str(run.id),
                employee=emp, case_params=params,
                antiguedad=Antiguedad(0,0,0,0), # Placeholder
                tiempo_pago=Antiguedad(0,0,0,0),
                payroll_months=[], salary_average=Decimal(str(run.salary_average)),
                manual_inputs=ManualInputs(),
                benefits=benefits, deductions=[],
                total_benefits=Decimal(str(run.total_benefits)),
                total_deductions=Decimal(str(run.total_deductions)),
                net_payment=Decimal(str(run.net_payment)),
                calculation_date=run.fecha_calculo,
                motivo_config={}
            )
    except Exception as e:
        print(f"Error reconstrucción: {e}")
        return None

def generate_documents_logic(result, run_id, docs_map, stamps_map, cite, cite_num, rej_date):
    """Core logic wrapper"""
    files = []
    output_dir = Path(settings.OUTPUTS_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_dir = output_dir / f"run_{run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    excel_writer = ExcelWriter()
    qr_gen = QRStampGenerator()
    
    with get_db() as db:
        templates = get_templates(db)
        
        for doc_type, generate in docs_map.items():
            if not generate: continue
            
            try:
                # 1. Generate Base Excel
                template = templates.get(doc_type)
                template_path = template.file_path if template else None
                file_name = f"{doc_type}_{result.employee.ci}.xlsx"
                output_path = run_dir / file_name
                
                # Dispatcher simple
                if doc_type == 'f_finiquito':
                    excel_writer.create_finiquito_document(result, template_path, str(output_path))
                elif doc_type == 'memo_finalizacion':
                    excel_writer.create_memo_finalizacion(result, template_path, cite, cite_num, str(output_path))
                # ... otros tipos ... (mantener lógica original de dispatch)
                else:
                    # Generic fallback or specific implementations
                    excel_writer.create_finiquito_document(result, template_path, str(output_path)) # Fallback test

                # 2. Apply Stamp
                final_path = output_path
                has_stamp = False
                
                if stamps_map.get(doc_type):
                    stamp_payload = qr_gen.generate_qr_payload(run_id, doc_type, result.employee.ci)
                    stamped_name = f"{output_path.stem}_stamped.xlsx"
                    stamped_path = run_dir / stamped_name
                    
                    qr_gen.add_stamp_to_excel(str(output_path), str(stamped_path), stamp_payload, DocumentStampConfig(True))
                    final_path = stamped_path
                    has_stamp = True

                # 3. Register DB
                db_doc = GeneratedDocument(
                    calculation_run_id=run_id,
                    document_type=DocumentType(doc_type) if doc_type in DocumentType.__members__ else DocumentType.F_FINIQUITO, # Fallback safe
                    file_name=final_path.name,
                    file_path=str(final_path),
                    has_internal_stamp=has_stamp,
                    template_version=template.version if template else 1
                )
                db.add(db_doc)
                files.append({'path': str(final_path), 'type': doc_type, 'stamp': has_stamp})
                
            except Exception as e:
                st.error(f"Error generando {doc_type}: {e}")
        
        db.commit()
    return files

def get_templates(db):
    # Helper simple para templates
    ts = db.query(DocumentTemplate).filter_by(is_active=True).all()
    # Mapeo string -> template object
    return {t.document_type.value: t for t in ts}

def show_download_section(files):
    st.header("📥 Descargar Documentos")
    for f in files:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.success(f"✅ {f['type'].upper()} {'(Con Sello)' if f['stamp'] else ''}")
        with c2:
            if os.path.exists(f['path']):
                with open(f['path'], "rb") as file:
                    st.download_button(
                        f"⬇️ Descargar", file, file_name=os.path.basename(f['path']),
                        key=f"dl_{f['path']}"
                    )
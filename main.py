"""
Main Streamlit Application for Finiquito Calculation System
Manages navigation, authentication, and page routing
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
from typing import Optional, Dict, Any

# Add app directory to path
sys.path.append(str(Path(__file__).parent))

# Import pages
from app.pages.upload_page import show as show_upload_page
from app.pages.mapping_page import show_mapping_page
from app.pages.case_selection_page import show_case_selection_page
from app.pages.preview_page import show_preview_page
from app.pages.generate_page import show_generate_page
from app.pages.case_history_page import show_case_history_page
from app.pages.case_detail_page import show_case_detail_page
from app.pages.admin_page import show_admin_page

# Import authentication and database
from app.auth.auth_handler import authenticate_user, check_permission
from infra.database.connection import get_db, init_database as init_db
from infra.database.models import (
    User, SystemConfig, AuditLog, CalculationRun, MotivoRetiroConfig
)

# Page configuration
st.set_page_config(
    page_title="Sistema de Cálculo de Finiquitos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'upload'
    if 'workflow_step' not in st.session_state:
        st.session_state.workflow_step = 1
    if 'calculation_run_id' not in st.session_state:
        st.session_state.calculation_run_id = None

# Page definitions with metadata
PAGES = {
    'upload': {
        'title': '📤 Cargar Archivos',
        'function': show_upload_page,
        'step': 1,
        'requires_auth': True,
        'min_role': 'viewer',
        'workflow': True
    },
    'mapping': {
        'title': '🔗 Mapeo de Columnas',
        'function': show_mapping_page,
        'step': 2,
        'requires_auth': True,
        'min_role': 'viewer',
        'workflow': True
    },
    'case_selection': {
        'title': '👤 Selección de Caso',
        'function': show_case_selection_page,
        'step': 3,
        'requires_auth': True,
        'min_role': 'viewer',
        'workflow': True
    },
    'preview': {
        'title': '📋 Vista Previa y Cálculo',
        'function': show_preview_page,
        'step': 4,
        'requires_auth': True,
        'min_role': 'operator',
        'workflow': True
    },
    'generate': {
        'title': '📄 Generar Documentos',
        'function': show_generate_page,
        'step': 5,
        'requires_auth': True,
        'min_role': 'operator',
        'workflow': True
    },
    'history': {
        'title': '📚 Historial de Casos',
        'function': show_case_history_page,
        'step': None,
        'requires_auth': True,
        'min_role': 'viewer',
        'workflow': False
    },
    'detail': {
        'title': '🔍 Detalle de Caso',
        'function': show_case_detail_page,
        'step': None,
        'requires_auth': True,
        'min_role': 'viewer',
        'workflow': False
    },
    'admin': {
        'title': '⚙️ Administración',
        'function': show_admin_page,
        'step': None,
        'requires_auth': True,
        'min_role': 'admin',
        'workflow': False
    }
}

# Role hierarchy
ROLE_HIERARCHY = {
    'viewer': 1,
    'operator': 2,
    'admin': 3
}

def check_role_permission(user_role: str, required_role: str) -> bool:
    """Check if user role meets minimum required role"""
    if not user_role or not required_role:
        return False
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 999)
    return user_level >= required_level

def render_login():
    """Render login page"""
    st.title("🔐 Sistema de Cálculo de Finiquitos")
    st.markdown("### Inicio de Sesión")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Usuario", key="login_username")
            password = st.text_input("Contraseña", type="password", key="login_password")
            submitted = st.form_submit_button("Ingresar", use_container_width=True)
            
            if submitted:
                if username and password:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.username = user['username']
                        st.session_state.user_role = user['role']
                        st.success(f"¡Bienvenido, {user['username']}!")
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos")
                else:
                    st.warning("Por favor ingrese usuario y contraseña")
        
        # Development mode hint
        with st.expander("🔧 Modo Desarrollo"):
            st.info("""
            **Usuarios de prueba:**
            - Admin: admin / admin123
            - Operador: operator / oper123
            - Visor: viewer / view123
            """)

def render_progress_indicator():
    """Render workflow progress indicator"""
    if st.session_state.get('current_page') in ['upload', 'mapping', 'case_selection', 'preview', 'generate']:
        workflow_pages = [k for k, v in PAGES.items() if v['workflow']]
        current_step = PAGES[st.session_state.current_page].get('step', 1)
        
        # Progress bar
        progress = (current_step - 1) / (len(workflow_pages) - 1)
        st.progress(progress)
        
        # Step indicators
        cols = st.columns(len(workflow_pages))
        for i, (page_key, col) in enumerate(zip(workflow_pages, cols)):
            page = PAGES[page_key]
            step_num = page['step']
            
            with col:
                if step_num < current_step:
                    st.markdown(f"✅ **Paso {step_num}**")
                    st.caption(page['title'].split(' ', 1)[1])
                elif step_num == current_step:
                    st.markdown(f"🔵 **Paso {step_num}**")
                    st.caption(page['title'].split(' ', 1)[1])
                else:
                    st.markdown(f"⭕ **Paso {step_num}**")
                    st.caption(page['title'].split(' ', 1)[1])
        
        st.markdown("---")

def render_sidebar():
    """Render sidebar navigation"""
    with st.sidebar:
        st.title("📊 Navegación")
        
        # User info
        if st.session_state.authenticated:
            st.success(f"👤 {st.session_state.username}")
            st.caption(f"Rol: {st.session_state.user_role}")
            
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                for key in ['authenticated', 'username', 'user_role']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
            
            st.markdown("---")
            
            # Workflow navigation
            st.subheader("Proceso de Cálculo")
            for page_key, page in PAGES.items():
                if page['workflow']:
                    if check_role_permission(st.session_state.user_role, page['min_role']):
                        if st.button(page['title'], 
                                   key=f"nav_{page_key}",
                                   use_container_width=True,
                                   disabled=(page_key == st.session_state.current_page)):
                            st.session_state.current_page = page_key
                            st.rerun()
            
            st.markdown("---")
            
            # Management navigation
            st.subheader("Gestión")
            for page_key, page in PAGES.items():
                if not page['workflow']:
                    if check_role_permission(st.session_state.user_role, page['min_role']):
                        if st.button(page['title'],
                                   key=f"nav_{page_key}",
                                   use_container_width=True,
                                   disabled=(page_key == st.session_state.current_page)):
                            st.session_state.current_page = page_key
                            st.rerun()
            
            # Quick actions
            st.markdown("---")
            st.subheader("Acciones Rápidas")
            
            if st.button("🆕 Nuevo Cálculo", use_container_width=True):
                # Clear workflow session state
                keys_to_clear = ['uploaded_files', 'dataframes', 'mappings', 
                               'selected_employee', 'case_params', 'calculation_result',
                               'calculation_run_id', 'generated_documents']
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.session_state.current_page = 'upload'
                st.rerun()
            
            if st.session_state.get('calculation_run_id'):
                if st.button("📋 Ver Caso Actual", use_container_width=True):
                    st.session_state.current_page = 'detail'
                    st.session_state.detail_case_id = st.session_state.calculation_run_id
                    st.rerun()

def render_main_content():
    """Render main content area based on current page"""
    current_page = st.session_state.current_page
    
    if current_page not in PAGES:
        st.error(f"Página no encontrada: {current_page}")
        return
    
    page = PAGES[current_page]
    
    # Check role permission
    if not check_role_permission(st.session_state.user_role, page['min_role']):
        st.error("⛔ No tiene permisos para acceder a esta página")
        st.info(f"Rol requerido: {page['min_role']}")
        return
    
    # Render progress indicator for workflow pages
    if page['workflow']:
        render_progress_indicator()
    
    # Render page content
    try:
        page['function']()
    except Exception as e:
        st.error(f"Error al cargar la página: {str(e)}")
        with st.expander("Detalles del error"):
            st.exception(e)

def initialize_system():
    """Initialize database and create default users if needed"""
    try:
        # Initialize database
        init_db()
        
        # Create default users if not exist
        with get_db() as db:
            # Check if admin user exists
            admin = db.query(User).filter_by(username='admin').first()
            if not admin:
                # Create default users
                default_users = [
                    User(username='admin', password_hash='admin123', role='ADMIN', 
                         email='admin@finiquito.app', created_by='system'),
                    User(username='operator', password_hash='oper123', role='OPERATOR',
                         email='operator@finiquito.app', created_by='system'),
                    User(username='viewer', password_hash='view123', role='VIEWER',
                         email='viewer@finiquito.app', created_by='system')
                ]
                
                for user in default_users:
                    db.add(user)
                
                db.commit()
                print("Default users created")
            # Create default motivos de retiro if not exist
            from config import BolivianLaborConstants
            motivo = db.query(MotivoRetiroConfig).first()
            if not motivo:
                default_motivos = []
                for code, config_data in BolivianLaborConstants.MOTIVO_RETIRO_TYPES.items():
                    default_motivos.append(MotivoRetiroConfig(
                        code=code,
                        description=config_data['description'],
                        dia_menos_flag=config_data['dia_menos_flag'],
                        indemnizacion_flag=config_data['indemnizacion_flag'],
                        aguinaldo_flag=config_data['aguinaldo_flag'],
                        desahucio_flag=config_data['desahucio_flag'],
                        vacaciones_flag=config_data['vacaciones_flag'],
                        is_active=True
                    ))
                
                for m in default_motivos:
                    db.add(m)
                
                db.commit()
                print("Default motivos de retiro created")
            
            # Create default system config if not exist
            config = db.query(SystemConfig).first()
            if not config:
                default_configs = [
                    SystemConfig(key='system_version', value='1.0.0', created_by='system'),
                    SystemConfig(key='max_upload_size_mb', value='50', created_by='system'),
                    SystemConfig(key='qr_stamp_enabled', value='true', created_by='system'),
                    SystemConfig(key='require_approval', value='false', created_by='system')
                ]
                
                for cfg in default_configs:
                    db.add(cfg)
                
                db.commit()
                print("Default configuration created")
                
    except Exception as e:
        print(f"Error initializing system: {e}")

def main():
    """Main application entry point"""
    # Initialize session state
    init_session_state()
    
    # Initialize system on first run
    if 'system_initialized' not in st.session_state:
        initialize_system()
        st.session_state.system_initialized = True
    
    # Authentication check
    if not st.session_state.authenticated:
        render_login()
    else:
        # Render navigation sidebar
        render_sidebar()
        
        # Render main content
        render_main_content()

if __name__ == "__main__":
    main()

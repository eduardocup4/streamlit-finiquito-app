"""
Main Streamlit application for Finiquito Calculator
"""
import streamlit as st
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import configuration
from config import settings, labor_constants

# Import pages
from app.pages import (
    upload_page,
    mapping_page,
    case_selection_page,
    preview_page,
    generate_page,
    case_history_page,
    case_detail_page,
    admin_page
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
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Upload"
    if 'calculation_data' not in st.session_state:
        st.session_state.calculation_data = {}
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {}
    if 'mapping_config' not in st.session_state:
        st.session_state.mapping_config = {}
    if 'selected_employee' not in st.session_state:
        st.session_state.selected_employee = None
    if 'calculation_result' not in st.session_state:
        st.session_state.calculation_result = None

init_session_state()

# Custom CSS
def load_custom_css():
    """Load custom CSS for styling"""
    st.markdown("""
    <style>
    /* Main container */
    .main {
        padding-top: 2rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        padding-top: 1rem;
    }
    
    /* Headers */
    h1 {
        color: #1e3a8a;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 10px;
    }
    
    h2 {
        color: #1e40af;
        margin-top: 2rem;
    }
    
    h3 {
        color: #1e40af;
    }
    
    /* Success messages */
    .stSuccess {
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
    }
    
    /* Error messages */
    .stError {
        background-color: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
    }
    
    /* Warning messages */
    .stWarning {
        background-color: #fff3cd;
        border-color: #ffeeba;
        color: #856404;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #3b82f6;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: background-color 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #2563eb;
    }
    
    /* Progress indicator */
    .progress-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
        padding: 1rem;
        background: #f0f9ff;
        border-radius: 10px;
    }
    
    .progress-step {
        flex: 1;
        text-align: center;
        padding: 0.5rem;
        margin: 0 0.25rem;
        border-radius: 5px;
        font-weight: 500;
    }
    
    .progress-step.active {
        background: #3b82f6;
        color: white;
    }
    
    .progress-step.completed {
        background: #10b981;
        color: white;
    }
    
    .progress-step.pending {
        background: #e5e7eb;
        color: #6b7280;
    }
    
    /* Table styling */
    table {
        width: 100%;
        border-collapse: collapse;
    }
    
    th {
        background-color: #f3f4f6;
        padding: 0.75rem;
        text-align: left;
        font-weight: 600;
    }
    
    td {
        padding: 0.75rem;
        border-bottom: 1px solid #e5e7eb;
    }
    
    /* Cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1e40af;
    }
    
    .metric-label {
        color: #6b7280;
        font-size: 0.875rem;
        margin-top: 0.25rem;
    }
    </style>
    """, unsafe_allow_html=True)

load_custom_css()

# Authentication
def show_login():
    """Show login form"""
    st.markdown("## 🔐 Inicio de Sesión")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="Ingrese su usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
            submitted = st.form_submit_button("Iniciar Sesión", use_container_width=True)
            
            if submitted:
                # Simple authentication (replace with proper authentication)
                if username == "admin" and password == settings.ADMIN_PASSWORD:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "admin"
                    st.rerun()
                elif username == "operator" and password == "operator123":
                    st.session_state.authenticated = True
                    st.session_state.user_role = "operator"
                    st.rerun()
                elif username == "viewer" and password == "viewer123":
                    st.session_state.authenticated = True
                    st.session_state.user_role = "viewer"
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
        
        st.info("**Demo credentials:**\n- Admin: admin / admin123\n- Operator: operator / operator123\n- Viewer: viewer / viewer123")

# Progress indicator
def show_progress_indicator():
    """Show progress indicator for multi-step process"""
    steps = [
        ("Upload", "📤"),
        ("Mapping", "🗺️"),
        ("Selección", "👤"),
        ("Preview", "👁️"),
        ("Generar", "📄"),
    ]
    
    current_step = st.session_state.current_page
    current_index = next((i for i, (step, _) in enumerate(steps) if step == current_step), 0)
    
    cols = st.columns(len(steps))
    for i, (step, icon) in enumerate(steps):
        with cols[i]:
            if i < current_index:
                st.markdown(f'<div class="progress-step completed">{icon} {step} ✓</div>', 
                           unsafe_allow_html=True)
            elif i == current_index:
                st.markdown(f'<div class="progress-step active">{icon} {step}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="progress-step pending">{icon} {step}</div>', 
                           unsafe_allow_html=True)

# Sidebar navigation
def show_sidebar():
    """Show sidebar with navigation"""
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50/3b82f6/ffffff?text=JELB+Solutions", 
                use_column_width=True)
        
        st.markdown("---")
        
        st.markdown(f"### 👤 Usuario: {st.session_state.user_role}")
        
        st.markdown("---")
        
        st.markdown("### 📋 Navegación")
        
        # Process pages
        if st.button("📤 Upload", use_container_width=True):
            st.session_state.current_page = "Upload"
        
        if st.button("🗺️ Mapping", use_container_width=True):
            st.session_state.current_page = "Mapping"
        
        if st.button("👤 Selección de Caso", use_container_width=True):
            st.session_state.current_page = "Case Selection"
        
        if st.button("👁️ Preview", use_container_width=True):
            st.session_state.current_page = "Preview"
        
        if st.button("📄 Generar", use_container_width=True):
            st.session_state.current_page = "Generate"
        
        st.markdown("---")
        
        # History and admin
        if st.button("📚 Historial de Casos", use_container_width=True):
            st.session_state.current_page = "History"
        
        if st.session_state.user_role == "admin":
            if st.button("⚙️ Administración", use_container_width=True):
                st.session_state.current_page = "Admin"
        
        st.markdown("---")
        
        # Logout
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.rerun()
        
        st.markdown("---")
        
        # Info
        st.markdown("### ℹ️ Información")
        st.markdown(f"**Versión:** {settings.APP_VERSION}")
        st.markdown(f"**© 2024 {settings.COMPANY_NAME}**")

# Main app
def main():
    """Main application logic"""
    if not st.session_state.authenticated:
        show_login()
    else:
        show_sidebar()
        
        # Header
        st.markdown(f"# {settings.APP_NAME}")
        
        # Show progress for process pages
        if st.session_state.current_page in ["Upload", "Mapping", "Case Selection", "Preview", "Generate"]:
            show_progress_indicator()
        
        # Route to appropriate page
        if st.session_state.current_page == "Upload":
            upload_page.show()
        elif st.session_state.current_page == "Mapping":
            mapping_page.show()
        elif st.session_state.current_page == "Case Selection":
            case_selection_page.show()
        elif st.session_state.current_page == "Preview":
            preview_page.show()
        elif st.session_state.current_page == "Generate":
            generate_page.show()
        elif st.session_state.current_page == "History":
            case_history_page.show()
        elif st.session_state.current_page == "Case Detail":
            case_detail_page.show()
        elif st.session_state.current_page == "Admin":
            admin_page.show()
        else:
            st.info("Seleccione una opción del menú lateral")

if __name__ == "__main__":
    main()

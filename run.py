#!/usr/bin/env python3
"""
Entry point for Finiquito Calculator Application
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Create necessary directories
from config import STORAGE_DIR, UPLOADS_DIR, OUTPUTS_DIR, TEMPLATES_DIR

for directory in [STORAGE_DIR, UPLOADS_DIR, OUTPUTS_DIR, TEMPLATES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Initialize database
from infra.database.connection import init_database
init_database()

# Run streamlit app
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    import sys
    
    sys.argv = ["streamlit", "run", str(project_root / "app" / "main.py")]
    sys.exit(stcli.main())

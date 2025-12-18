"""
Database models for the Finiquito application
"""
from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, 
    Text, ForeignKey, JSON, Enum, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

class CaseStatus(enum.Enum):
    DRAFT = "draft"
    CALCULATED = "calculated"
    GENERATED = "generated"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"

class DocumentType(enum.Enum):
    F_FINIQUITO = "f_finiquito"
    MEMO_FINALIZACION = "memo_finalizacion"
    RECHAZO_POST = "rechazo_post"
    F_SALIDA = "f_salida"
    F_EQUIPOS = "f_equipos"
    CONTABLE_PREVIEW = "contable_preview"

# User management
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.OPERATOR)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    email = Column(String(255), nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    calculation_runs = relationship("CalculationRun", back_populates="created_by_user")

# Company homologation
class CompanyHomologation(Base):
    __tablename__ = "company_homologations"
    
    id = Column(Integer, primary_key=True)
    alias = Column(String(200), unique=True, nullable=False)
    normalized_name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    __table_args__ = (
        Index('idx_company_alias', 'alias'),
        Index('idx_normalized_name', 'normalized_name'),
    )

# Motivo retiro configuration
class MotivoRetiroConfig(Base):
    __tablename__ = "motivo_retiro_configs"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(String(200), nullable=False)
    dia_menos_flag = Column(Boolean, default=False)
    indemnizacion_flag = Column(Boolean, default=False)
    aguinaldo_flag = Column(Boolean, default=True)
    desahucio_flag = Column(Boolean, default=False)
    vacaciones_flag = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Template management
class DocumentTemplate(Base):
    __tablename__ = "document_templates"
    
    id = Column(Integer, primary_key=True)
    document_type = Column(Enum(DocumentType), nullable=False)
    version = Column(Integer, default=1)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    uploaded_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('document_type', 'version', name='uq_template_version'),
        Index('idx_template_type', 'document_type'),
    )

# Field mapping profiles
class MappingProfile(Base):
    __tablename__ = "mapping_profiles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    payroll_mappings = Column(JSON, nullable=False)  # {"ci": "Nro. Doc", "nombre": "Nombres", ...}
    rdp_mappings = Column(JSON, nullable=False)
    include_otros_bonos = Column(Boolean, default=False)
    otros_bonos_column = Column(String(100))
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Main calculation run (case)
class CalculationRun(Base):
    __tablename__ = "calculation_runs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Employee info
    employee_ci = Column(String(50), nullable=False)
    employee_name = Column(String(200), nullable=False)
    employee_empresa = Column(String(200), nullable=False)
    
    # Case parameters
    pay_until_date = Column(DateTime, nullable=False)
    request_date = Column(DateTime, nullable=False)
    motivo_retiro = Column(String(50), nullable=False)
    quinquenio_start_date = Column(DateTime)
    aguinaldo_excluded = Column(Boolean, default=False)
    
    # Status
    status = Column(Enum(CaseStatus), default=CaseStatus.DRAFT)
    
    # Calculation results
    calculation_data = Column(JSON)  # Store all calculation details
    total_benefits = Column(Float)
    total_deductions = Column(Float)
    net_payment = Column(Float)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Input tracking
    input_files_hash = Column(String(64))  # SHA256 of input files
    mapping_profile_id = Column(Integer, ForeignKey("mapping_profiles.id"))
    template_versions_used = Column(JSON)  # {"f_finiquito": 1, "memo": 2, ...}
    
    # Additional metadata
    observaciones = Column(Text)
    aprobado_por = Column(String(100))
    fecha_pago = Column(DateTime)
    medio_pago = Column(String(100))
    nro_comprobante = Column(String(100))
    
    # Relationships
    created_by_user = relationship("User", back_populates="calculation_runs")
    mapping_profile = relationship("MappingProfile")
    generated_documents = relationship("GeneratedDocument", back_populates="calculation_run")
    
    __table_args__ = (
        Index('idx_employee_ci', 'employee_ci'),
        Index('idx_employee_empresa', 'employee_empresa'),
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
    )

# Generated documents
class GeneratedDocument(Base):
    __tablename__ = "generated_documents"
    
    id = Column(Integer, primary_key=True)
    calculation_run_id = Column(String(36), ForeignKey("calculation_runs.id"), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    template_version = Column(Integer)
    has_internal_stamp = Column(Boolean, default=False)
    qr_payload = Column(String(500))
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    calculation_run = relationship("CalculationRun", back_populates="generated_documents")
    
    __table_args__ = (
        Index('idx_calc_run', 'calculation_run_id'),
        Index('idx_doc_type', 'document_type'),
    )

# Manual input storage
class ManualInput(Base):
    __tablename__ = "manual_inputs"
    
    id = Column(Integer, primary_key=True)
    calculation_run_id = Column(String(36), ForeignKey("calculation_runs.id"), nullable=False)
    input_type = Column(String(50), nullable=False)  # 'bono_refrigerio', 'comision', 'otros', 'deduccion'
    label = Column(String(200))
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_calc_run_inputs', 'calculation_run_id'),
    )

# Audit log
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(String(100))
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_timestamp', 'timestamp'),
    )

# System configuration
class SystemConfig(Base):
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    value_type = Column(String(20))  # 'string', 'integer', 'float', 'boolean', 'json'
    description = Column(Text)
    is_sensitive = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)

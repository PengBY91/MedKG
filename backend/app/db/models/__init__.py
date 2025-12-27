from sqlalchemy import Column, String, Integer, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class PolicyDocument(Base):
    """政策文档模型"""
    __tablename__ = "policy_documents"
    
    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_size = Column(Integer)
    file_path = Column(String)  # 文件存储路径
    uploaded_by = Column(String)
    status = Column(String)  # processing, completed, failed
    category = Column(String)
    tags = Column(Text)  # JSON array
    total_chars = Column(Integer)
    chunks_count = Column(Integer)
    extracted_rules_count = Column(Integer, default=0)
    extracted_rules = Column(Text)  # JSON array
    extracted_entities = Column(Text)  # JSON array
    preview_text = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

class Rule(Base):
    """规则模型"""
    __tablename__ = "rules"
    
    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    shacl_content = Column(Text)
    status = Column(String)  # draft, valid, invalid
    policy_id = Column(String, ForeignKey("policy_documents.id"))
    created_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Terminology(Base):
    """术语模型"""
    __tablename__ = "terminology"
    
    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    raw_term = Column(String, nullable=False)
    standard_code = Column(String)
    standard_name = Column(String)
    code_system = Column(String)  # SNOMED-CT, ICD-10, etc.
    confidence = Column(Float)
    status = Column(String)  # pending, approved, rejected
    reviewed_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class DataAsset(Base):
    """数据资产模型"""
    __tablename__ = "data_assets"
    
    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    type = Column(String)  # table, view, file
    description = Column(Text)
    schema_info = Column(Text)  # JSON
    quality_score = Column(Float)
    owner = Column(String)
    tags = Column(Text)  # JSON array
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class WorkflowDefinition(Base):
    """工作流定义模型"""
    __tablename__ = "workflow_definitions"
    
    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    type = Column(String)  # terminology_review, rule_approval, governance_pipeline
    version = Column(Integer, default=1)
    nodes = Column(Text)  # JSON array
    transitions = Column(Text)  # JSON array
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class WorkflowInstance(Base):
    """工作流实例模型"""
    __tablename__ = "workflow_instances"
    
    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    definition_id = Column(String, ForeignKey("workflow_definitions.id"))
    status = Column(String)  # running, completed, failed
    current_node = Column(String)
    context = Column(Text)  # JSON
    initiator = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

class WorkflowTask(Base):
    """工作流任务模型"""
    __tablename__ = "workflow_tasks"
    
    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    instance_id = Column(String, ForeignKey("workflow_instances.id"))
    node_id = Column(String)
    type = Column(String)  # approval, review, input
    status = Column(String)  # pending, assigned, in_progress, completed, rejected
    assignee = Column(String)
    data = Column(Text)  # JSON
    result = Column(String)
    comments = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

class GovernanceTask(Base):
    """人机协同治理任务模型 (ReviewTask)"""
    __tablename__ = "governance_tasks"
    
    id = Column(String, primary_key=True)
    doc_id = Column(String, ForeignKey("policy_documents.id"))
    tenant_id = Column(String, nullable=False, index=True, default="default")
    status = Column(String)  # pending, approved, rejected, corrected, auto_approved
    task_type = Column(String)  # general, rule_review, term_review
    extracted_data = Column(Text)  # JSON
    final_data = Column(Text)  # JSON
    confidence = Column(Float)
    reviewer_id = Column(String)
    feedback_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    email = Column(String)
    full_name = Column(String)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    role = Column(String)
    status = Column(String)  # active, inactive
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Tenant(Base):
    """租户模型"""
    __tablename__ = "tenants"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False, index=True)
    type = Column(String)  # hospital, government, clinic
    status = Column(String, default="active")
    config = Column(Text)  # JSON
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class StandardizationTask(Base):
    """标准化任务模型"""
    __tablename__ = "standardization_tasks"
    
    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True, default="system")
    filename = Column(String, nullable=False)
    status = Column(String)  # processing, completed, failed
    user = Column(String)
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    results = Column(Text)  # JSON array
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

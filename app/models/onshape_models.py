from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(24), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(String(24))
    owner_name = Column(String(255))
    public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    workspaces = relationship("Workspace", back_populates="document")
    elements = relationship("Element", back_populates="document")


class Workspace(Base):
    __tablename__ = "workspaces"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(24), unique=True, index=True, nullable=False)
    document_id = Column(String(24), ForeignKey("documents.document_id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_main = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="workspaces")


class Element(Base):
    __tablename__ = "elements"
    
    id = Column(Integer, primary_key=True, index=True)
    element_id = Column(String(24), unique=True, index=True, nullable=False)
    document_id = Column(String(24), ForeignKey("documents.document_id"), nullable=False)
    name = Column(String(255), nullable=False)
    element_type = Column(String(50))  # PARTSTUDIO, ASSEMBLY, DRAWING, etc.
    data_type = Column(String(50))
    thumbnail_id = Column(String(24))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="elements")
    parts = relationship("Part", back_populates="element")
    features = relationship("Feature", back_populates="element")


class Part(Base):
    __tablename__ = "parts"
    
    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(String(24), unique=True, index=True, nullable=False)
    element_id = Column(String(24), ForeignKey("elements.element_id"), nullable=False)
    name = Column(String(255), nullable=False)
    state = Column(String(50))  # IN_PROGRESS, RELEASED, etc.
    body_type = Column(String(50))  # solid, surface, etc.
    material_properties = Column(JSON)
    mass_properties = Column(JSON)
    appearance = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    element = relationship("Element", back_populates="parts")


class Feature(Base):
    __tablename__ = "features"
    
    id = Column(Integer, primary_key=True, index=True)
    feature_id = Column(String(24), unique=True, index=True, nullable=False)
    element_id = Column(String(24), ForeignKey("elements.element_id"), nullable=False)
    name = Column(String(255), nullable=False)
    feature_type = Column(String(100))  # extrude, revolve, etc.
    suppressed = Column(Boolean, default=False)
    parameters = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    element = relationship("Element", back_populates="features")


class Assembly(Base):
    __tablename__ = "assemblies"
    
    id = Column(Integer, primary_key=True, index=True)
    assembly_id = Column(String(24), unique=True, index=True, nullable=False)
    element_id = Column(String(24), ForeignKey("elements.element_id"), nullable=False)
    name = Column(String(255), nullable=False)
    root_assembly = Column(JSON)
    sub_assemblies = Column(JSON)
    instances = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SyncLog(Base):
    __tablename__ = "sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    sync_type = Column(String(50), nullable=False)  # documents, parts, features, etc.
    status = Column(String(20), nullable=False)  # success, error, in_progress
    message = Column(Text)
    records_processed = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    sync_metadata = Column(JSON) 
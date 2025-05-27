from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DocumentBase(BaseModel):
    document_id: str = Field(..., description="Onshape document ID")
    name: str = Field(..., description="Document name")
    description: Optional[str] = None
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    public: bool = False


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WorkspaceBase(BaseModel):
    workspace_id: str = Field(..., description="Onshape workspace ID")
    document_id: str = Field(..., description="Parent document ID")
    name: str = Field(..., description="Workspace name")
    description: Optional[str] = None
    is_main: bool = False


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceResponse(WorkspaceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ElementBase(BaseModel):
    element_id: str = Field(..., description="Onshape element ID")
    document_id: str = Field(..., description="Parent document ID")
    name: str = Field(..., description="Element name")
    element_type: Optional[str] = None
    data_type: Optional[str] = None
    thumbnail_id: Optional[str] = None


class ElementCreate(ElementBase):
    pass


class ElementResponse(ElementBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PartBase(BaseModel):
    part_id: str = Field(..., description="Onshape part ID")
    element_id: str = Field(..., description="Parent element ID")
    name: str = Field(..., description="Part name")
    state: Optional[str] = None
    body_type: Optional[str] = None
    material_properties: Optional[Dict[str, Any]] = None
    mass_properties: Optional[Dict[str, Any]] = None
    appearance: Optional[Dict[str, Any]] = None


class PartCreate(PartBase):
    pass


class PartResponse(PartBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FeatureBase(BaseModel):
    feature_id: str = Field(..., description="Onshape feature ID")
    element_id: str = Field(..., description="Parent element ID")
    name: str = Field(..., description="Feature name")
    feature_type: Optional[str] = None
    suppressed: bool = False
    parameters: Optional[Dict[str, Any]] = None


class FeatureCreate(FeatureBase):
    pass


class FeatureResponse(FeatureBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AssemblyBase(BaseModel):
    assembly_id: str = Field(..., description="Onshape assembly ID")
    element_id: str = Field(..., description="Parent element ID")
    name: str = Field(..., description="Assembly name")
    root_assembly: Optional[Dict[str, Any]] = None
    sub_assemblies: Optional[Dict[str, Any]] = None
    instances: Optional[Dict[str, Any]] = None


class AssemblyCreate(AssemblyBase):
    pass


class AssemblyResponse(AssemblyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SyncLogBase(BaseModel):
    sync_type: str = Field(..., description="Type of sync operation")
    status: str = Field(..., description="Sync status")
    message: Optional[str] = None
    records_processed: int = 0
    errors_count: int = 0
    metadata: Optional[Dict[str, Any]] = None


class SyncLogCreate(SyncLogBase):
    pass


class SyncLogResponse(SyncLogBase):
    id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SyncRequest(BaseModel):
    sync_type: str = Field(..., description="Type of data to sync")
    document_ids: Optional[List[str]] = Field(None, description="Specific document IDs to sync")
    force_refresh: bool = Field(False, description="Force refresh of existing data")


class OnshapeDocumentInfo(BaseModel):
    """Schema for Onshape document information from API"""
    id: str
    name: str
    description: Optional[str] = None
    owner: Optional[Dict[str, Any]] = None
    public: bool = False
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    elements: Optional[List[Dict[str, Any]]] = None 
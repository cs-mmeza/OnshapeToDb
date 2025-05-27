from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from app.database import get_db
from app.models.onshape_models import Document, Workspace, Element, Part, Feature, SyncLog
from app.schemas.onshape_schemas import (
    DocumentResponse, WorkspaceResponse, ElementResponse, 
    PartResponse, FeatureResponse, SyncLogResponse, SyncRequest
)
from app.services.onshape_client import OnshapeClient
from app.services.sync_service import SyncService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Onshape API service is running"}


@router.get("/onshape/test-connection")
async def test_onshape_connection():
    """Test connection to Onshape API"""
    try:
        client = OnshapeClient()
        is_connected = client.test_connection()
        
        if is_connected:
            user_info = client.get_user_info()
            return {
                "status": "connected",
                "message": "Successfully connected to Onshape API",
                "user": user_info
            }
        else:
            return {
                "status": "failed",
                "message": "Failed to connect to Onshape API"
            }
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Document endpoints
@router.get("/documents", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all documents from database"""
    documents = db.query(Document).offset(skip).limit(limit).all()
    return documents


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get specific document by ID"""
    document = db.query(Document).filter(Document.document_id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/documents/{document_id}/workspaces", response_model=List[WorkspaceResponse])
async def get_document_workspaces(document_id: str, db: Session = Depends(get_db)):
    """Get workspaces for a specific document"""
    workspaces = db.query(Workspace).filter(Workspace.document_id == document_id).all()
    return workspaces


@router.get("/documents/{document_id}/elements", response_model=List[ElementResponse])
async def get_document_elements(document_id: str, db: Session = Depends(get_db)):
    """Get elements for a specific document"""
    elements = db.query(Element).filter(Element.document_id == document_id).all()
    return elements


# Workspace endpoints
@router.get("/workspaces", response_model=List[WorkspaceResponse])
async def get_workspaces(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all workspaces from database"""
    workspaces = db.query(Workspace).offset(skip).limit(limit).all()
    return workspaces


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: str, db: Session = Depends(get_db)):
    """Get specific workspace by ID"""
    workspace = db.query(Workspace).filter(Workspace.workspace_id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


# Element endpoints
@router.get("/elements", response_model=List[ElementResponse])
async def get_elements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    element_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all elements from database"""
    query = db.query(Element)
    if element_type:
        query = query.filter(Element.element_type == element_type)
    elements = query.offset(skip).limit(limit).all()
    return elements


@router.get("/elements/{element_id}", response_model=ElementResponse)
async def get_element(element_id: str, db: Session = Depends(get_db)):
    """Get specific element by ID"""
    element = db.query(Element).filter(Element.element_id == element_id).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    return element


@router.get("/elements/{element_id}/parts", response_model=List[PartResponse])
async def get_element_parts(element_id: str, db: Session = Depends(get_db)):
    """Get parts for a specific element"""
    parts = db.query(Part).filter(Part.element_id == element_id).all()
    return parts


@router.get("/elements/{element_id}/features", response_model=List[FeatureResponse])
async def get_element_features(element_id: str, db: Session = Depends(get_db)):
    """Get features for a specific element"""
    features = db.query(Feature).filter(Feature.element_id == element_id).all()
    return features


# Part endpoints
@router.get("/parts", response_model=List[PartResponse])
async def get_parts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all parts from database"""
    parts = db.query(Part).offset(skip).limit(limit).all()
    return parts


@router.get("/parts/{part_id}", response_model=PartResponse)
async def get_part(part_id: str, db: Session = Depends(get_db)):
    """Get specific part by ID"""
    part = db.query(Part).filter(Part.part_id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    return part


# Feature endpoints
@router.get("/features", response_model=List[FeatureResponse])
async def get_features(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    feature_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all features from database"""
    query = db.query(Feature)
    if feature_type:
        query = query.filter(Feature.feature_type == feature_type)
    features = query.offset(skip).limit(limit).all()
    return features


@router.get("/features/{feature_id}", response_model=FeatureResponse)
async def get_feature(feature_id: str, db: Session = Depends(get_db)):
    """Get specific feature by ID"""
    feature = db.query(Feature).filter(Feature.feature_id == feature_id).first()
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    return feature


# Sync endpoints
@router.post("/sync/documents")
async def sync_documents(
    background_tasks: BackgroundTasks,
    force_refresh: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Sync documents from Onshape API"""
    try:
        sync_service = SyncService(db)
        
        # Run sync in background for large operations
        def run_sync():
            return sync_service.sync_documents(force_refresh=force_refresh)
        
        background_tasks.add_task(run_sync)
        
        return {
            "status": "started",
            "message": "Document sync started in background"
        }
    except Exception as e:
        logger.error(f"Document sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/workspaces/{document_id}")
async def sync_workspaces(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Sync workspaces for a specific document"""
    try:
        sync_service = SyncService(db)
        
        def run_sync():
            return sync_service.sync_document_workspaces(document_id)
        
        background_tasks.add_task(run_sync)
        
        return {
            "status": "started",
            "message": f"Workspace sync started for document {document_id}"
        }
    except Exception as e:
        logger.error(f"Workspace sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/elements/{document_id}/{workspace_id}")
async def sync_elements(
    document_id: str,
    workspace_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Sync elements for a specific document workspace"""
    try:
        sync_service = SyncService(db)
        
        def run_sync():
            return sync_service.sync_document_elements(document_id, workspace_id)
        
        background_tasks.add_task(run_sync)
        
        return {
            "status": "started",
            "message": f"Element sync started for document {document_id}"
        }
    except Exception as e:
        logger.error(f"Element sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/parts/{document_id}/{workspace_id}/{element_id}")
async def sync_parts(
    document_id: str,
    workspace_id: str,
    element_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Sync parts for a specific element"""
    try:
        sync_service = SyncService(db)
        
        def run_sync():
            return sync_service.sync_parts(document_id, workspace_id, element_id)
        
        background_tasks.add_task(run_sync)
        
        return {
            "status": "started",
            "message": f"Parts sync started for element {element_id}"
        }
    except Exception as e:
        logger.error(f"Parts sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/features/{document_id}/{workspace_id}/{element_id}")
async def sync_features(
    document_id: str,
    workspace_id: str,
    element_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Sync features for a specific element"""
    try:
        sync_service = SyncService(db)
        
        def run_sync():
            return sync_service.sync_features(document_id, workspace_id, element_id)
        
        background_tasks.add_task(run_sync)
        
        return {
            "status": "started",
            "message": f"Features sync started for element {element_id}"
        }
    except Exception as e:
        logger.error(f"Features sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/full")
async def full_sync(
    background_tasks: BackgroundTasks,
    document_ids: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """Perform a full sync of all data"""
    try:
        sync_service = SyncService(db)
        
        def run_sync():
            return sync_service.full_sync(document_ids=document_ids)
        
        background_tasks.add_task(run_sync)
        
        return {
            "status": "started",
            "message": "Full sync started in background"
        }
    except Exception as e:
        logger.error(f"Full sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Sync logs endpoints
@router.get("/sync/logs", response_model=List[SyncLogResponse])
async def get_sync_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sync_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get sync logs"""
    query = db.query(SyncLog)
    if sync_type:
        query = query.filter(SyncLog.sync_type == sync_type)
    if status:
        query = query.filter(SyncLog.status == status)
    
    logs = query.order_by(SyncLog.started_at.desc()).offset(skip).limit(limit).all()
    return logs


@router.get("/sync/logs/{log_id}", response_model=SyncLogResponse)
async def get_sync_log(log_id: int, db: Session = Depends(get_db)):
    """Get specific sync log by ID"""
    log = db.query(SyncLog).filter(SyncLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Sync log not found")
    return log


# Export endpoints
@router.get("/export/stl/{document_id}/{workspace_id}/{element_id}/{part_id}")
async def export_part_stl(
    document_id: str,
    workspace_id: str,
    element_id: str,
    part_id: str,
    units: str = Query("meter", regex="^(meter|millimeter|centimeter|inch|foot|yard)$")
):
    """Export part as STL file"""
    try:
        client = OnshapeClient()
        stl_data = client.export_stl(document_id, workspace_id, element_id, part_id, units)
        
        from fastapi.responses import Response
        return Response(
            content=stl_data,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename=part_{part_id}.stl"}
        )
    except Exception as e:
        logger.error(f"STL export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Statistics endpoints
@router.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """Get database statistics"""
    try:
        stats = {
            "documents": db.query(Document).count(),
            "workspaces": db.query(Workspace).count(),
            "elements": db.query(Element).count(),
            "parts": db.query(Part).count(),
            "features": db.query(Feature).count(),
            "sync_logs": db.query(SyncLog).count()
        }
        
        # Get recent sync logs
        recent_syncs = db.query(SyncLog).order_by(SyncLog.started_at.desc()).limit(5).all()
        stats["recent_syncs"] = [
            {
                "id": log.id,
                "sync_type": log.sync_type,
                "status": log.status,
                "started_at": log.started_at,
                "records_processed": log.records_processed
            }
            for log in recent_syncs
        ]
        
        return stats
    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
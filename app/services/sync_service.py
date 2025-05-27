from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.services.onshape_client import OnshapeClient
from app.models.onshape_models import (
    Document, Workspace, Element, Part, Feature, Assembly, SyncLog
)
from app.schemas.onshape_schemas import (
    DocumentCreate, WorkspaceCreate, ElementCreate, 
    PartCreate, FeatureCreate, AssemblyCreate, SyncLogCreate
)

logger = logging.getLogger(__name__)


class SyncService:
    """Service for synchronizing Onshape data with local database"""
    
    def __init__(self, db: Session):
        self.db = db
        self.onshape_client = OnshapeClient()
    
    def _create_sync_log(self, sync_type: str, status: str = "in_progress", 
                        message: str = None) -> SyncLog:
        """Create a sync log entry"""
        sync_log = SyncLog(
            sync_type=sync_type,
            status=status,
            message=message,
            started_at=datetime.utcnow()
        )
        self.db.add(sync_log)
        self.db.commit()
        self.db.refresh(sync_log)
        return sync_log
    
    def _update_sync_log(self, sync_log: SyncLog, status: str, 
                        records_processed: int = 0, errors_count: int = 0,
                        message: str = None):
        """Update sync log with completion status"""
        sync_log.status = status
        sync_log.records_processed = records_processed
        sync_log.errors_count = errors_count
        sync_log.completed_at = datetime.utcnow()
        if message:
            sync_log.message = message
        self.db.commit()
    
    def sync_documents(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Sync documents from Onshape"""
        sync_log = self._create_sync_log("documents", message="Starting document sync")
        
        try:
            # Get documents from Onshape
            response = self.onshape_client.get_documents(limit=100)
            documents_data = response.get('items', [])
            
            processed = 0
            errors = 0
            
            for doc_data in documents_data:
                try:
                    document_id = doc_data.get('id')
                    if not document_id:
                        continue
                    
                    # Check if document already exists
                    existing_doc = self.db.query(Document).filter(
                        Document.document_id == document_id
                    ).first()
                    
                    if existing_doc and not force_refresh:
                        continue
                    
                    # Get detailed document info
                    detailed_doc = self.onshape_client.get_document(document_id)
                    
                    # Extract owner information
                    owner_info = detailed_doc.get('owner', {})
                    owner_id = owner_info.get('id') if owner_info else None
                    owner_name = owner_info.get('name') if owner_info else None
                    
                    if existing_doc:
                        # Update existing document
                        existing_doc.name = detailed_doc.get('name', '')
                        existing_doc.description = detailed_doc.get('description')
                        existing_doc.owner_id = owner_id
                        existing_doc.owner_name = owner_name
                        existing_doc.public = detailed_doc.get('public', False)
                        existing_doc.updated_at = datetime.utcnow()
                    else:
                        # Create new document
                        document = Document(
                            document_id=document_id,
                            name=detailed_doc.get('name', ''),
                            description=detailed_doc.get('description'),
                            owner_id=owner_id,
                            owner_name=owner_name,
                            public=detailed_doc.get('public', False)
                        )
                        self.db.add(document)
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing document {doc_data.get('id')}: {str(e)}")
                    errors += 1
            
            self.db.commit()
            self._update_sync_log(sync_log, "success", processed, errors, 
                                f"Synced {processed} documents")
            
            return {
                "status": "success",
                "processed": processed,
                "errors": errors,
                "message": f"Successfully synced {processed} documents"
            }
            
        except Exception as e:
            logger.error(f"Document sync failed: {str(e)}")
            self._update_sync_log(sync_log, "error", 0, 1, str(e))
            return {
                "status": "error",
                "message": str(e)
            }
    
    def sync_document_workspaces(self, document_id: str) -> Dict[str, Any]:
        """Sync workspaces for a specific document"""
        sync_log = self._create_sync_log("workspaces", 
                                       message=f"Starting workspace sync for document {document_id}")
        
        try:
            # Get workspaces from Onshape
            response = self.onshape_client.get_document_workspaces(document_id)
            workspaces_data = response
            
            processed = 0
            errors = 0
            
            for workspace_data in workspaces_data:
                try:
                    workspace_id = workspace_data.get('id')
                    if not workspace_id:
                        continue
                    
                    # Check if workspace already exists
                    existing_workspace = self.db.query(Workspace).filter(
                        Workspace.workspace_id == workspace_id
                    ).first()
                    
                    if existing_workspace:
                        # Update existing workspace
                        existing_workspace.name = workspace_data.get('name', '')
                        existing_workspace.description = workspace_data.get('description')
                        existing_workspace.is_main = workspace_data.get('isMain', False)
                        existing_workspace.updated_at = datetime.utcnow()
                    else:
                        # Create new workspace
                        workspace = Workspace(
                            workspace_id=workspace_id,
                            document_id=document_id,
                            name=workspace_data.get('name', ''),
                            description=workspace_data.get('description'),
                            is_main=workspace_data.get('isMain', False)
                        )
                        self.db.add(workspace)
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing workspace {workspace_data.get('id')}: {str(e)}")
                    errors += 1
            
            self.db.commit()
            self._update_sync_log(sync_log, "success", processed, errors,
                                f"Synced {processed} workspaces for document {document_id}")
            
            return {
                "status": "success",
                "processed": processed,
                "errors": errors,
                "message": f"Successfully synced {processed} workspaces"
            }
            
        except Exception as e:
            logger.error(f"Workspace sync failed: {str(e)}")
            self._update_sync_log(sync_log, "error", 0, 1, str(e))
            return {
                "status": "error",
                "message": str(e)
            }
    
    def sync_document_elements(self, document_id: str, workspace_id: str) -> Dict[str, Any]:
        """Sync elements for a specific document workspace"""
        sync_log = self._create_sync_log("elements", 
                                       message=f"Starting element sync for document {document_id}")
        
        try:
            # Get elements from Onshape
            response = self.onshape_client.get_document_elements(document_id, workspace_id)
            elements_data = response
            
            processed = 0
            errors = 0
            
            for element_data in elements_data:
                try:
                    element_id = element_data.get('id')
                    if not element_id:
                        continue
                    
                    # Check if element already exists
                    existing_element = self.db.query(Element).filter(
                        Element.element_id == element_id
                    ).first()
                    
                    if existing_element:
                        # Update existing element
                        existing_element.name = element_data.get('name', '')
                        existing_element.element_type = element_data.get('elementType')
                        existing_element.data_type = element_data.get('dataType')
                        existing_element.thumbnail_id = element_data.get('thumbnailId')
                        existing_element.updated_at = datetime.utcnow()
                    else:
                        # Create new element
                        element = Element(
                            element_id=element_id,
                            document_id=document_id,
                            name=element_data.get('name', ''),
                            element_type=element_data.get('elementType'),
                            data_type=element_data.get('dataType'),
                            thumbnail_id=element_data.get('thumbnailId')
                        )
                        self.db.add(element)
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing element {element_data.get('id')}: {str(e)}")
                    errors += 1
            
            self.db.commit()
            self._update_sync_log(sync_log, "success", processed, errors,
                                f"Synced {processed} elements for document {document_id}")
            
            return {
                "status": "success",
                "processed": processed,
                "errors": errors,
                "message": f"Successfully synced {processed} elements"
            }
            
        except Exception as e:
            logger.error(f"Element sync failed: {str(e)}")
            self._update_sync_log(sync_log, "error", 0, 1, str(e))
            return {
                "status": "error",
                "message": str(e)
            }
    
    def sync_parts(self, document_id: str, workspace_id: str, element_id: str) -> Dict[str, Any]:
        """Sync parts for a specific part studio"""
        sync_log = self._create_sync_log("parts", 
                                       message=f"Starting parts sync for element {element_id}")
        
        try:
            # Get parts from Onshape
            response = self.onshape_client.get_parts(document_id, workspace_id, element_id)
            parts_data = response
            
            processed = 0
            errors = 0
            
            for part_data in parts_data:
                try:
                    part_id = part_data.get('partId')
                    if not part_id:
                        continue
                    
                    # Check if part already exists
                    existing_part = self.db.query(Part).filter(
                        Part.part_id == part_id
                    ).first()
                    
                    # Get mass properties if available
                    mass_properties = None
                    try:
                        mass_props_response = self.onshape_client.get_part_mass_properties(
                            document_id, workspace_id, element_id, part_id
                        )
                        mass_properties = mass_props_response
                    except Exception:
                        pass  # Mass properties might not be available
                    
                    if existing_part:
                        # Update existing part
                        existing_part.name = part_data.get('name', '')
                        existing_part.state = part_data.get('state')
                        existing_part.body_type = part_data.get('bodyType')
                        existing_part.material_properties = part_data.get('materialProperties')
                        existing_part.mass_properties = mass_properties
                        existing_part.appearance = part_data.get('appearance')
                        existing_part.updated_at = datetime.utcnow()
                    else:
                        # Create new part
                        part = Part(
                            part_id=part_id,
                            element_id=element_id,
                            name=part_data.get('name', ''),
                            state=part_data.get('state'),
                            body_type=part_data.get('bodyType'),
                            material_properties=part_data.get('materialProperties'),
                            mass_properties=mass_properties,
                            appearance=part_data.get('appearance')
                        )
                        self.db.add(part)
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing part {part_data.get('partId')}: {str(e)}")
                    errors += 1
            
            self.db.commit()
            self._update_sync_log(sync_log, "success", processed, errors,
                                f"Synced {processed} parts for element {element_id}")
            
            return {
                "status": "success",
                "processed": processed,
                "errors": errors,
                "message": f"Successfully synced {processed} parts"
            }
            
        except Exception as e:
            logger.error(f"Parts sync failed: {str(e)}")
            self._update_sync_log(sync_log, "error", 0, 1, str(e))
            return {
                "status": "error",
                "message": str(e)
            }
    
    def sync_features(self, document_id: str, workspace_id: str, element_id: str) -> Dict[str, Any]:
        """Sync features for a specific part studio"""
        sync_log = self._create_sync_log("features", 
                                       message=f"Starting features sync for element {element_id}")
        
        try:
            # Get features from Onshape
            response = self.onshape_client.get_features(document_id, workspace_id, element_id)
            features_data = response.get('features', [])
            
            processed = 0
            errors = 0
            
            for feature_data in features_data:
                try:
                    feature_id = feature_data.get('featureId')
                    if not feature_id:
                        continue
                    
                    # Check if feature already exists
                    existing_feature = self.db.query(Feature).filter(
                        Feature.feature_id == feature_id
                    ).first()
                    
                    if existing_feature:
                        # Update existing feature
                        existing_feature.name = feature_data.get('name', '')
                        existing_feature.feature_type = feature_data.get('featureType')
                        existing_feature.suppressed = feature_data.get('suppressed', False)
                        existing_feature.parameters = feature_data.get('parameters')
                        existing_feature.updated_at = datetime.utcnow()
                    else:
                        # Create new feature
                        feature = Feature(
                            feature_id=feature_id,
                            element_id=element_id,
                            name=feature_data.get('name', ''),
                            feature_type=feature_data.get('featureType'),
                            suppressed=feature_data.get('suppressed', False),
                            parameters=feature_data.get('parameters')
                        )
                        self.db.add(feature)
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing feature {feature_data.get('featureId')}: {str(e)}")
                    errors += 1
            
            self.db.commit()
            self._update_sync_log(sync_log, "success", processed, errors,
                                f"Synced {processed} features for element {element_id}")
            
            return {
                "status": "success",
                "processed": processed,
                "errors": errors,
                "message": f"Successfully synced {processed} features"
            }
            
        except Exception as e:
            logger.error(f"Features sync failed: {str(e)}")
            self._update_sync_log(sync_log, "error", 0, 1, str(e))
            return {
                "status": "error",
                "message": str(e)
            }
    
    def full_sync(self, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Perform a full sync of documents and their data"""
        sync_log = self._create_sync_log("full_sync", message="Starting full sync")
        
        try:
            total_processed = 0
            total_errors = 0
            results = {}
            
            # Sync documents first
            doc_result = self.sync_documents()
            results['documents'] = doc_result
            total_processed += doc_result.get('processed', 0)
            total_errors += doc_result.get('errors', 0)
            
            # Get documents to sync
            if document_ids:
                documents = self.db.query(Document).filter(
                    Document.document_id.in_(document_ids)
                ).all()
            else:
                documents = self.db.query(Document).limit(10).all()  # Limit for demo
            
            for document in documents:
                # Sync workspaces
                workspace_result = self.sync_document_workspaces(document.document_id)
                total_processed += workspace_result.get('processed', 0)
                total_errors += workspace_result.get('errors', 0)
                
                # Get main workspace
                main_workspace = self.db.query(Workspace).filter(
                    Workspace.document_id == document.document_id,
                    Workspace.is_main == True
                ).first()
                
                if main_workspace:
                    # Sync elements
                    elements_result = self.sync_document_elements(
                        document.document_id, main_workspace.workspace_id
                    )
                    total_processed += elements_result.get('processed', 0)
                    total_errors += elements_result.get('errors', 0)
                    
                    # Sync parts and features for each element
                    elements = self.db.query(Element).filter(
                        Element.document_id == document.document_id
                    ).all()
                    
                    for element in elements:
                        if element.element_type == 'PARTSTUDIO':
                            # Sync parts
                            parts_result = self.sync_parts(
                                document.document_id, main_workspace.workspace_id, element.element_id
                            )
                            total_processed += parts_result.get('processed', 0)
                            total_errors += parts_result.get('errors', 0)
                            
                            # Sync features
                            features_result = self.sync_features(
                                document.document_id, main_workspace.workspace_id, element.element_id
                            )
                            total_processed += features_result.get('processed', 0)
                            total_errors += features_result.get('errors', 0)
            
            self._update_sync_log(sync_log, "success", total_processed, total_errors,
                                f"Full sync completed: {total_processed} records processed")
            
            return {
                "status": "success",
                "total_processed": total_processed,
                "total_errors": total_errors,
                "results": results,
                "message": f"Full sync completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Full sync failed: {str(e)}")
            self._update_sync_log(sync_log, "error", 0, 1, str(e))
            return {
                "status": "error",
                "message": str(e)
            } 
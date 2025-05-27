import hashlib
import hmac
import base64
import requests
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional, List
import secrets
import string
from app.config import settings


class OnshapeClient:
    """Client for interacting with Onshape API"""
    
    def __init__(self):
        self.base_url = settings.onshape_base_url
        self.access_key = settings.onshape_access_key
        self.secret_key = settings.onshape_secret_key
        self.api_version = "v6"
    
    def _generate_nonce(self, length: int = 25) -> str:
        """Generate a random nonce for API authentication"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def _create_signature(self, method: str, url: str, nonce: str, 
                         auth_date: str, content_type: str) -> str:
        """Create HMAC signature for Onshape API authentication"""
        parsed_url = urlparse(url)
        url_path = parsed_url.path
        url_query = parsed_url.query if parsed_url.query else ''
        
        # Create string to sign
        string_to_sign = (
            f"{method}\n"
            f"{nonce}\n"
            f"{auth_date}\n"
            f"{content_type}\n"
            f"{url_path}\n"
            f"{url_query}\n"
        ).lower()
        
        # Create HMAC signature
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Encode in base64
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        return f"On {self.access_key}:HmacSHA256:{signature_b64}"
    
    def _make_request(self, method: str, endpoint: str, 
                     params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Onshape API"""
        url = f"{self.base_url}/{self.api_version}/{endpoint}"
        
        # Generate authentication headers
        nonce = self._generate_nonce()
        auth_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        content_type = 'application/json' if data else ''
        
        headers = {
            'Date': auth_date,
            'On-Nonce': nonce,
            'Authorization': self._create_signature(method, url, nonce, auth_date, content_type),
            'Accept': 'application/json'
        }
        
        if content_type:
            headers['Content-Type'] = content_type
        
        # Make request
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, params=params, 
                                       json=data if data else None)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Onshape API request failed: {str(e)}")
    
    def get_documents(self, query: Optional[str] = None, 
                     owner_type: int = 0, sort_column: str = "name",
                     sort_order: str = "asc", offset: int = 0, 
                     limit: int = 20) -> Dict[str, Any]:
        """Get list of documents"""
        params = {
            'q': query,
            'ownerType': owner_type,
            'sortColumn': sort_column,
            'sortOrder': sort_order,
            'offset': offset,
            'limit': limit
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        return self._make_request('GET', 'documents', params=params)
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get specific document information"""
        return self._make_request('GET', f'documents/{document_id}')
    
    def get_document_workspaces(self, document_id: str) -> Dict[str, Any]:
        """Get workspaces for a document"""
        return self._make_request('GET', f'documents/d/{document_id}/workspaces')
    
    def get_document_elements(self, document_id: str, workspace_id: str) -> Dict[str, Any]:
        """Get elements in a document workspace"""
        return self._make_request('GET', f'documents/d/{document_id}/w/{workspace_id}/elements')
    
    def get_parts(self, document_id: str, workspace_id: str, element_id: str) -> Dict[str, Any]:
        """Get parts from a part studio"""
        return self._make_request('GET', 
            f'partstudios/d/{document_id}/w/{workspace_id}/e/{element_id}/parts')
    
    def get_features(self, document_id: str, workspace_id: str, element_id: str) -> Dict[str, Any]:
        """Get features from a part studio"""
        return self._make_request('GET', 
            f'partstudios/d/{document_id}/w/{workspace_id}/e/{element_id}/features')
    
    def get_assembly(self, document_id: str, workspace_id: str, element_id: str) -> Dict[str, Any]:
        """Get assembly information"""
        return self._make_request('GET', 
            f'assemblies/d/{document_id}/w/{workspace_id}/e/{element_id}')
    
    def get_assembly_definition(self, document_id: str, workspace_id: str, 
                               element_id: str) -> Dict[str, Any]:
        """Get assembly definition"""
        return self._make_request('GET', 
            f'assemblies/d/{document_id}/w/{workspace_id}/e/{element_id}/definition')
    
    def get_part_mass_properties(self, document_id: str, workspace_id: str, 
                                element_id: str, part_id: str) -> Dict[str, Any]:
        """Get mass properties for a part"""
        params = {'partId': part_id}
        return self._make_request('GET', 
            f'partstudios/d/{document_id}/w/{workspace_id}/e/{element_id}/massproperties',
            params=params)
    
    def export_stl(self, document_id: str, workspace_id: str, element_id: str,
                   part_id: str, units: str = "meter") -> bytes:
        """Export part as STL"""
        url = f"{self.base_url}/{self.api_version}/partstudios/d/{document_id}/w/{workspace_id}/e/{element_id}/stl"
        
        params = {
            'partId': part_id,
            'units': units
        }
        
        # Generate authentication headers
        nonce = self._generate_nonce()
        auth_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        content_type = 'application/json'
        
        headers = {
            'Date': auth_date,
            'On-Nonce': nonce,
            'Authorization': self._create_signature('GET', url, nonce, auth_date, content_type),
            'Accept': 'application/octet-stream'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            raise Exception(f"STL export failed: {str(e)}")
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information"""
        return self._make_request('GET', 'users/current')
    
    def test_connection(self) -> bool:
        """Test if the API connection is working"""
        try:
            self.get_user_info()
            return True
        except Exception:
            return False 
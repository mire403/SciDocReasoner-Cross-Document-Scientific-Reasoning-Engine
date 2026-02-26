"""Storage utilities for structured data persistence"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class StructuredStorage:
    """Manages structured storage of intermediate results"""
    
    def __init__(self, base_dir: str = "data/storage"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def save_document(self, doc_id: str, document: Dict[str, Any]) -> Path:
        """Save parsed document"""
        doc_dir = self.base_dir / "documents"
        doc_dir.mkdir(exist_ok=True)
        file_path = doc_dir / f"{doc_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(document, f, indent=2, ensure_ascii=False)
        return file_path
    
    def save_entities(self, doc_id: str, entities: List[Dict[str, Any]]) -> Path:
        """Save extracted entities"""
        entities_dir = self.base_dir / "entities"
        entities_dir.mkdir(exist_ok=True)
        file_path = entities_dir / f"{doc_id}_entities.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(entities, f, indent=2, ensure_ascii=False)
        return file_path
    
    def save_claims(self, doc_id: str, claims: List[Dict[str, Any]]) -> Path:
        """Save extracted claims"""
        claims_dir = self.base_dir / "claims"
        claims_dir.mkdir(exist_ok=True)
        file_path = claims_dir / f"{doc_id}_claims.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(claims, f, indent=2, ensure_ascii=False)
        return file_path
    
    def save_graph(self, graph_data: Dict[str, Any], name: str = "main") -> Path:
        """Save graph structure"""
        graph_dir = self.base_dir / "graphs"
        graph_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = graph_dir / f"{name}_{timestamp}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        return file_path
    
    def load_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Load parsed document"""
        file_path = self.base_dir / "documents" / f"{doc_id}.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def load_entities(self, doc_id: str) -> Optional[List[Dict[str, Any]]]:
        """Load extracted entities"""
        file_path = self.base_dir / "entities" / f"{doc_id}_entities.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def load_claims(self, doc_id: str) -> Optional[List[Dict[str, Any]]]:
        """Load extracted claims"""
        file_path = self.base_dir / "claims" / f"{doc_id}_claims.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

"""Graph schema definitions"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class NodeType(str, Enum):
    """Types of nodes in the reasoning graph"""
    DOCUMENT = "document"
    ENTITY = "entity"
    CLAIM = "claim"
    HYPOTHESIS = "hypothesis"


class EdgeType(str, Enum):
    """Types of edges in the reasoning graph"""
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    EXTENDS = "extends"
    BASED_ON = "based_on"
    MENTIONS = "mentions"
    CONTAINS = "contains"
    LINKS_TO = "links_to"


class GraphNode(BaseModel):
    """Represents a node in the reasoning graph"""
    node_id: str
    node_type: NodeType
    properties: Dict[str, Any] = {}


class GraphEdge(BaseModel):
    """Represents an edge in the reasoning graph"""
    source_id: str
    target_id: str
    edge_type: EdgeType
    properties: Dict[str, Any] = {}
    weight: float = 1.0  # Confidence or strength


class GraphSchema:
    """Schema for the semantic reasoning graph"""
    
    @staticmethod
    def get_node_schema(node_type: NodeType) -> Dict[str, Any]:
        """Get schema for a node type"""
        schemas = {
            NodeType.DOCUMENT: {
                "required": ["doc_id", "title"],
                "optional": ["authors", "abstract", "metadata"]
            },
            NodeType.ENTITY: {
                "required": ["entity_id", "text", "entity_type"],
                "optional": ["doc_id", "context", "canonical_name"]
            },
            NodeType.CLAIM: {
                "required": ["claim_id", "text", "claim_type"],
                "optional": ["doc_id", "sentence_id", "entities", "confidence"]
            },
            NodeType.HYPOTHESIS: {
                "required": ["hypothesis_id", "text"],
                "optional": ["doc_id", "supporting_claims", "confidence", "source"]
            }
        }
        return schemas.get(node_type, {})
    
    @staticmethod
    def get_edge_schema(edge_type: EdgeType) -> Dict[str, Any]:
        """Get schema for an edge type"""
        schemas = {
            EdgeType.SUPPORTS: {
                "description": "Claim or evidence supports a hypothesis",
                "allowed_source": [NodeType.CLAIM, NodeType.ENTITY],
                "allowed_target": [NodeType.HYPOTHESIS, NodeType.CLAIM]
            },
            EdgeType.CONTRADICTS: {
                "description": "Claim contradicts another claim or hypothesis",
                "allowed_source": [NodeType.CLAIM],
                "allowed_target": [NodeType.CLAIM, NodeType.HYPOTHESIS]
            },
            EdgeType.EXTENDS: {
                "description": "Claim extends or builds upon another claim",
                "allowed_source": [NodeType.CLAIM],
                "allowed_target": [NodeType.CLAIM]
            },
            EdgeType.BASED_ON: {
                "description": "Hypothesis or claim is based on evidence",
                "allowed_source": [NodeType.ENTITY, NodeType.CLAIM],
                "allowed_target": [NodeType.HYPOTHESIS, NodeType.CLAIM]
            },
            EdgeType.MENTIONS: {
                "description": "Claim or document mentions an entity",
                "allowed_source": [NodeType.CLAIM, NodeType.DOCUMENT],
                "allowed_target": [NodeType.ENTITY]
            },
            EdgeType.CONTAINS: {
                "description": "Document contains claims/entities/hypotheses",
                "allowed_source": [NodeType.DOCUMENT],
                "allowed_target": [NodeType.CLAIM, NodeType.ENTITY, NodeType.HYPOTHESIS]
            },
            EdgeType.LINKS_TO: {
                "description": "Entities are linked across documents",
                "allowed_source": [NodeType.ENTITY],
                "allowed_target": [NodeType.ENTITY]
            }
        }
        return schemas.get(edge_type, {})

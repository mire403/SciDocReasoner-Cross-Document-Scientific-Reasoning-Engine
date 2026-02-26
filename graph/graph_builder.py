"""Build semantic reasoning graph from extracted data"""

import networkx as nx
from typing import List, Dict, Any, Optional
from .graph_schema import (
    NodeType, EdgeType, GraphNode, GraphEdge, GraphSchema
)
from collections import defaultdict


class GraphBuilder:
    """Build multi-document semantic reasoning graph"""
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.schema = GraphSchema()
    
    def build_from_documents(
        self,
        documents: List[Dict[str, Any]],
        entities: List[Dict[str, Any]],
        claims: List[Dict[str, Any]],
        hypotheses: List[Dict[str, Any]],
        entity_links: Optional[Dict[str, List[str]]] = None
    ) -> nx.MultiDiGraph:
        """
        Build graph from extracted data
        
        Args:
            documents: List of parsed documents
            entities: List of extracted entities
            claims: List of extracted claims
            hypotheses: List of detected hypotheses
            entity_links: Dictionary mapping canonical entity names to entity IDs
        """
        self.graph = nx.MultiDiGraph()
        
        # Add document nodes
        for doc in documents:
            self._add_document_node(doc)
        
        # Add entity nodes
        entity_id_to_node = {}
        for entity in entities:
            node_id = self._add_entity_node(entity)
            entity_id_to_node[entity.get("entity_id", "")] = node_id
        
        # Link entities across documents
        if entity_links:
            self._link_entities(entity_links, entity_id_to_node)
        
        # Add claim nodes
        claim_id_to_node = {}
        for claim in claims:
            node_id = self._add_claim_node(claim)
            claim_id_to_node[claim.get("claim_id", "")] = node_id
            
            # Link claim to document
            doc_id = claim.get("doc_id", "")
            if doc_id:
                self._add_edge(
                    f"doc_{doc_id}",
                    node_id,
                    EdgeType.CONTAINS
                )
            
            # Link claim to entities
            entity_ids = claim.get("entities", [])
            for ent_id in entity_ids:
                if ent_id in entity_id_to_node:
                    self._add_edge(
                        node_id,
                        entity_id_to_node[ent_id],
                        EdgeType.MENTIONS
                    )
        
        # Add hypothesis nodes
        hypothesis_id_to_node = {}
        for hypothesis in hypotheses:
            node_id = self._add_hypothesis_node(hypothesis)
            hypothesis_id_to_node[hypothesis.get("hypothesis_id", "")] = node_id
            
            # Link hypothesis to document
            doc_id = hypothesis.get("doc_id", "")
            if doc_id:
                self._add_edge(
                    f"doc_{doc_id}",
                    node_id,
                    EdgeType.CONTAINS
                )
            
            # Link hypothesis to supporting claims
            supporting_claims = hypothesis.get("supporting_claims", [])
            for claim_id in supporting_claims:
                if claim_id in claim_id_to_node:
                    self._add_edge(
                        claim_id_to_node[claim_id],
                        node_id,
                        EdgeType.SUPPORTS,
                        weight=hypothesis.get("confidence", 0.5)
                    )
        
        # Infer relationships between claims
        self._infer_claim_relationships(claims, claim_id_to_node)
        
        return self.graph
    
    def _add_document_node(self, doc: Dict[str, Any]) -> str:
        """Add a document node to the graph"""
        doc_id = doc.get("doc_id", "")
        node_id = f"doc_{doc_id}"
        
        self.graph.add_node(
            node_id,
            node_type=NodeType.DOCUMENT,
            title=doc.get("title", ""),
            authors=doc.get("authors", []),
            abstract=doc.get("abstract", ""),
            metadata=doc.get("metadata", {})
        )
        
        return node_id
    
    def _add_entity_node(self, entity: Dict[str, Any]) -> str:
        """Add an entity node to the graph"""
        entity_id = entity.get("entity_id", "")
        node_id = f"ent_{entity_id}"
        
        self.graph.add_node(
            node_id,
            node_type=NodeType.ENTITY,
            text=entity.get("text", ""),
            entity_type=entity.get("entity_type", ""),
            doc_id=entity.get("doc_id", ""),
            context=entity.get("context", "")
        )
        
        return node_id
    
    def _add_claim_node(self, claim: Dict[str, Any]) -> str:
        """Add a claim node to the graph"""
        claim_id = claim.get("claim_id", "")
        node_id = f"claim_{claim_id}"
        
        self.graph.add_node(
            node_id,
            node_type=NodeType.CLAIM,
            text=claim.get("text", ""),
            claim_type=claim.get("claim_type", ""),
            doc_id=claim.get("doc_id", ""),
            sentence_id=claim.get("sentence_id", ""),
            confidence=claim.get("confidence", 0.5)
        )
        
        return node_id
    
    def _add_hypothesis_node(self, hypothesis: Dict[str, Any]) -> str:
        """Add a hypothesis node to the graph"""
        hyp_id = hypothesis.get("hypothesis_id", "")
        node_id = f"hyp_{hyp_id}"
        
        self.graph.add_node(
            node_id,
            node_type=NodeType.HYPOTHESIS,
            text=hypothesis.get("text", ""),
            doc_id=hypothesis.get("doc_id", ""),
            confidence=hypothesis.get("confidence", 0.5),
            source=hypothesis.get("source", "explicit")
        )
        
        return node_id
    
    def _add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None
    ):
        """Add an edge to the graph"""
        if not self.graph.has_node(source_id) or not self.graph.has_node(target_id):
            return
        
        self.graph.add_edge(
            source_id,
            target_id,
            edge_type=edge_type.value,
            weight=weight,
            properties=properties or {}
        )
    
    def _link_entities(
        self,
        entity_links: Dict[str, List[str]],
        entity_id_to_node: Dict[str, str]
    ):
        """Link entities across documents"""
        for canonical_name, entity_ids in entity_links.items():
            # Create edges between all pairs of linked entities
            node_ids = [
                entity_id_to_node.get(eid)
                for eid in entity_ids
                if eid in entity_id_to_node
            ]
            
            for i, node_id1 in enumerate(node_ids):
                for node_id2 in node_ids[i+1:]:
                    if node_id1 and node_id2:
                        self._add_edge(
                            node_id1,
                            node_id2,
                            EdgeType.LINKS_TO,
                            weight=1.0
                        )
    
    def _infer_claim_relationships(
        self,
        claims: List[Dict[str, Any]],
        claim_id_to_node: Dict[str, str]
    ):
        """Infer relationships between claims"""
        # Group claims by document
        claims_by_doc = defaultdict(list)
        for claim in claims:
            doc_id = claim.get("doc_id", "")
            claims_by_doc[doc_id].append(claim)
        
        # Simple heuristic: claims with similar entities might be related
        for doc_id, doc_claims in claims_by_doc.items():
            for i, claim1 in enumerate(doc_claims):
                claim1_id = claim1.get("claim_id", "")
                claim1_entities = set(claim1.get("entities", []))
                claim1_type = claim1.get("claim_type", "")
                
                if claim1_id not in claim_id_to_node:
                    continue
                
                node_id1 = claim_id_to_node[claim1_id]
                
                for claim2 in doc_claims[i+1:]:
                    claim2_id = claim2.get("claim_id", "")
                    claim2_entities = set(claim2.get("entities", []))
                    claim2_type = claim2.get("claim_type", "")
                    
                    if claim2_id not in claim_id_to_node:
                        continue
                    
                    node_id2 = claim_id_to_node[claim2_id]
                    
                    # Check for entity overlap
                    overlap = claim1_entities & claim2_entities
                    if overlap:
                        # If same type and overlapping entities, might extend
                        if claim1_type == claim2_type and len(overlap) >= 2:
                            self._add_edge(
                                node_id2,
                                node_id1,
                                EdgeType.EXTENDS,
                                weight=0.6
                            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary format for storage"""
        nodes = []
        edges = []
        
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "node_id": node_id,
                "node_type": data.get("node_type", "").value if hasattr(data.get("node_type", ""), "value") else str(data.get("node_type", "")),
                "properties": {k: v for k, v in data.items() if k != "node_type"}
            })
        
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                "source_id": source,
                "target_id": target,
                "edge_type": data.get("edge_type", ""),
                "weight": data.get("weight", 1.0),
                "properties": data.get("properties", {})
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "num_nodes": len(nodes),
            "num_edges": len(edges)
        }
    
    def from_dict(self, graph_data: Dict[str, Any]) -> nx.MultiDiGraph:
        """Load graph from dictionary format"""
        self.graph = nx.MultiDiGraph()
        
        # Add nodes
        for node_data in graph_data.get("nodes", []):
            node_id = node_data["node_id"]
            node_type = NodeType(node_data["node_type"])
            properties = node_data.get("properties", {})
            
            self.graph.add_node(node_id, node_type=node_type, **properties)
        
        # Add edges
        for edge_data in graph_data.get("edges", []):
            self.graph.add_edge(
                edge_data["source_id"],
                edge_data["target_id"],
                edge_type=edge_data.get("edge_type", ""),
                weight=edge_data.get("weight", 1.0),
                properties=edge_data.get("properties", {})
            )
        
        return self.graph

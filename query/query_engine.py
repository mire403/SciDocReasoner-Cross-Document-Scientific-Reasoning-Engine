"""Query engine for semantic reasoning graph"""

from typing import List, Dict, Any, Optional, Set
import networkx as nx
from ..graph.graph_schema import NodeType, EdgeType


def _is_node_type(node_data: Dict[str, Any], target_type: NodeType) -> bool:
    """Helper function to check node type (handles both enum and string)"""
    node_type = node_data.get("node_type")
    if isinstance(node_type, NodeType):
        return node_type == target_type
    elif isinstance(node_type, str):
        return node_type == target_type.value
    elif hasattr(node_type, 'value'):
        return node_type.value == target_type.value
    return False


class QueryEngine:
    """Query engine for the semantic reasoning graph"""
    
    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph
    
    def query_hypothesis_support(
        self,
        hypothesis_id: Optional[str] = None,
        hypothesis_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query 1: Find which papers/claims support or contradict a hypothesis
        
        Returns:
            Dictionary with supporting and contradicting claims/documents
        """
        # Find hypothesis node
        hyp_node_id = self._find_hypothesis_node(hypothesis_id, hypothesis_text)
        if not hyp_node_id:
            return {
                "hypothesis": None,
                "supporting": [],
                "contradicting": [],
                "documents": []
            }
        
        hyp_data = self.graph.nodes[hyp_node_id]
        
        # Find supporting claims
        supporting_claims = []
        supporting_docs = set()
        
        for predecessor in self.graph.predecessors(hyp_node_id):
            edge_data = self.graph.get_edge_data(predecessor, hyp_node_id)
            for edge_key, data in edge_data.items():
                if data.get("edge_type") == EdgeType.SUPPORTS.value:
                    pred_data = self.graph.nodes[predecessor]
                    if _is_node_type(pred_data, NodeType.CLAIM):
                        supporting_claims.append({
                            "claim_id": predecessor,
                            "text": pred_data.get("text", ""),
                            "doc_id": pred_data.get("doc_id", ""),
                            "confidence": data.get("weight", 1.0)
                        })
                        doc_id = pred_data.get("doc_id", "")
                        if doc_id:
                            supporting_docs.add(doc_id)
        
        # Find contradicting claims
        contradicting_claims = []
        contradicting_docs = set()
        
        for successor in self.graph.successors(hyp_node_id):
            edge_data = self.graph.get_edge_data(hyp_node_id, successor)
            for edge_key, data in edge_data.items():
                if data.get("edge_type") == EdgeType.CONTRADICTS.value:
                    succ_data = self.graph.nodes[successor]
                    if _is_node_type(succ_data, NodeType.CLAIM):
                        contradicting_claims.append({
                            "claim_id": successor,
                            "text": succ_data.get("text", ""),
                            "doc_id": succ_data.get("doc_id", ""),
                            "confidence": data.get("weight", 1.0)
                        })
                        doc_id = succ_data.get("doc_id", "")
                        if doc_id:
                            contradicting_docs.add(doc_id)
        
        # Get document info
        documents = []
        for doc_id in supporting_docs | contradicting_docs:
            doc_node_id = f"doc_{doc_id}"
            if self.graph.has_node(doc_node_id):
                doc_data = self.graph.nodes[doc_node_id]
                documents.append({
                    "doc_id": doc_id,
                    "title": doc_data.get("title", ""),
                    "supports": doc_id in supporting_docs,
                    "contradicts": doc_id in contradicting_docs
                })
        
        return {
            "hypothesis": {
                "hypothesis_id": hyp_node_id,
                "text": hyp_data.get("text", ""),
                "confidence": hyp_data.get("confidence", 0.5),
                "source": hyp_data.get("source", "explicit")
            },
            "supporting": supporting_claims,
            "contradicting": contradicting_claims,
            "documents": documents
        }
    
    def query_entity_evolution(
        self,
        entity_name: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query 2: Find the research evolution path of an entity
        
        Returns:
            Dictionary with evolution timeline and related claims
        """
        # Find entity node(s)
        entity_nodes = self._find_entity_nodes(entity_name, entity_id)
        if not entity_nodes:
            return {
                "entity": None,
                "evolution_path": [],
                "related_claims": [],
                "related_hypotheses": []
            }
        
        # Get canonical entity name
        canonical_name = entity_name or self.graph.nodes[entity_nodes[0]].get("text", "")
        
        # Find all claims mentioning this entity
        related_claims = []
        claim_timeline = []
        
        for ent_node_id in entity_nodes:
            # Find claims that mention this entity
            for successor in self.graph.successors(ent_node_id):
                edge_data = self.graph.get_edge_data(ent_node_id, successor)
                for edge_key, data in edge_data.items():
                    if data.get("edge_type") == EdgeType.MENTIONS.value:
                        succ_data = self.graph.nodes[successor]
                        if _is_node_type(succ_data, NodeType.CLAIM):
                            claim_info = {
                                "claim_id": successor,
                                "text": succ_data.get("text", ""),
                                "doc_id": succ_data.get("doc_id", ""),
                                "claim_type": succ_data.get("claim_type", ""),
                                "confidence": succ_data.get("confidence", 0.5)
                            }
                            related_claims.append(claim_info)
                            claim_timeline.append(claim_info)
            
            # Also check reverse (claims -> entities)
            for predecessor in self.graph.predecessors(ent_node_id):
                edge_data = self.graph.get_edge_data(predecessor, ent_node_id)
                for edge_key, data in edge_data.items():
                    if data.get("edge_type") == EdgeType.MENTIONS.value:
                        pred_data = self.graph.nodes[predecessor]
                        if _is_node_type(pred_data, NodeType.CLAIM):
                            claim_info = {
                                "claim_id": predecessor,
                                "text": pred_data.get("text", ""),
                                "doc_id": pred_data.get("doc_id", ""),
                                "claim_type": pred_data.get("claim_type", ""),
                                "confidence": pred_data.get("confidence", 0.5)
                            }
                            if claim_info not in related_claims:
                                related_claims.append(claim_info)
                                claim_timeline.append(claim_info)
        
        # Sort by document (simple evolution path)
        claim_timeline.sort(key=lambda x: x.get("doc_id", ""))
        
        # Find related hypotheses
        related_hypotheses = []
        for claim in related_claims:
            claim_node_id = claim["claim_id"]
            for successor in self.graph.successors(claim_node_id):
                edge_data = self.graph.get_edge_data(claim_node_id, successor)
                for edge_key, data in edge_data.items():
                    if data.get("edge_type") == EdgeType.SUPPORTS.value:
                        succ_data = self.graph.nodes[successor]
                        if _is_node_type(succ_data, NodeType.HYPOTHESIS):
                            hyp_info = {
                                "hypothesis_id": successor,
                                "text": succ_data.get("text", ""),
                                "doc_id": succ_data.get("doc_id", ""),
                                "confidence": succ_data.get("confidence", 0.5)
                            }
                            if hyp_info not in related_hypotheses:
                                related_hypotheses.append(hyp_info)
        
        return {
            "entity": {
                "name": canonical_name,
                "entity_ids": entity_nodes
            },
            "evolution_path": claim_timeline,
            "related_claims": related_claims,
            "related_hypotheses": related_hypotheses
        }
    
    def query_unvalidated_hypotheses(
        self,
        min_support: int = 2,
        max_contradictions: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Query 3: Find hypotheses that are not well-validated
        
        Returns:
            List of hypotheses with low support or high contradictions
        """
        unvalidated = []
        
        # Get all hypothesis nodes
        hyp_nodes = [
            node_id for node_id, data in self.graph.nodes(data=True)
            if _is_node_type(data, NodeType.HYPOTHESIS)
        ]
        
        for hyp_node_id in hyp_nodes:
            hyp_data = self.graph.nodes[hyp_node_id]
            
            # Count supporting claims
            supporting_count = 0
            for predecessor in self.graph.predecessors(hyp_node_id):
                edge_data = self.graph.get_edge_data(predecessor, hyp_node_id)
                for edge_key, data in edge_data.items():
                    if data.get("edge_type") == EdgeType.SUPPORTS.value:
                        if _is_node_type(self.graph.nodes[predecessor], NodeType.CLAIM):
                            supporting_count += 1
            
            # Count contradicting claims
            contradicting_count = 0
            for successor in self.graph.successors(hyp_node_id):
                edge_data = self.graph.get_edge_data(hyp_node_id, successor)
                for edge_key, data in edge_data.items():
                    if data.get("edge_type") == EdgeType.CONTRADICTS.value:
                        if _is_node_type(self.graph.nodes[successor], NodeType.CLAIM):
                            contradicting_count += 1
            
            # Check if unvalidated
            if supporting_count < min_support or contradicting_count > max_contradictions:
                unvalidated.append({
                    "hypothesis_id": hyp_node_id,
                    "text": hyp_data.get("text", ""),
                    "doc_id": hyp_data.get("doc_id", ""),
                    "supporting_count": supporting_count,
                    "contradicting_count": contradicting_count,
                    "confidence": hyp_data.get("confidence", 0.5),
                    "source": hyp_data.get("source", "explicit"),
                    "reason": "low_support" if supporting_count < min_support else "high_contradictions"
                })
        
        return unvalidated
    
    def query_claim_relationships(
        self,
        claim_id: Optional[str] = None,
        claim_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query 4: Find relationships between claims (supports, contradicts, extends)
        
        Returns:
            Dictionary with related claims and relationship types
        """
        # Find claim node
        claim_node_id = self._find_claim_node(claim_id, claim_text)
        if not claim_node_id:
            return {
                "claim": None,
                "related_claims": []
            }
        
        claim_data = self.graph.nodes[claim_node_id]
        related_claims = []
        
        # Find claims that this claim supports
        for successor in self.graph.successors(claim_node_id):
            edge_data = self.graph.get_edge_data(claim_node_id, successor)
            for edge_key, data in edge_data.items():
                edge_type = data.get("edge_type", "")
                succ_data = self.graph.nodes[successor]
                
                if succ_data.get("node_type") == NodeType.CLAIM:
                    related_claims.append({
                        "claim_id": successor,
                        "text": succ_data.get("text", ""),
                        "relationship": edge_type,
                        "direction": "outgoing",
                        "weight": data.get("weight", 1.0)
                    })
                elif succ_data.get("node_type") == NodeType.HYPOTHESIS:
                    related_claims.append({
                        "hypothesis_id": successor,
                        "text": succ_data.get("text", ""),
                        "relationship": edge_type,
                        "direction": "outgoing",
                        "weight": data.get("weight", 1.0)
                    })
        
        # Find claims that support/contradict/extend this claim
        for predecessor in self.graph.predecessors(claim_node_id):
            edge_data = self.graph.get_edge_data(predecessor, claim_node_id)
            for edge_key, data in edge_data.items():
                edge_type = data.get("edge_type", "")
                pred_data = self.graph.nodes[predecessor]
                
                if pred_data.get("node_type") == NodeType.CLAIM:
                    related_claims.append({
                        "claim_id": predecessor,
                        "text": pred_data.get("text", ""),
                        "relationship": edge_type,
                        "direction": "incoming",
                        "weight": data.get("weight", 1.0)
                    })
        
        return {
            "claim": {
                "claim_id": claim_node_id,
                "text": claim_data.get("text", ""),
                "claim_type": claim_data.get("claim_type", ""),
                "doc_id": claim_data.get("doc_id", "")
            },
            "related_claims": related_claims
        }
    
    def _find_hypothesis_node(
        self,
        hypothesis_id: Optional[str],
        hypothesis_text: Optional[str]
    ) -> Optional[str]:
        """Find hypothesis node by ID or text"""
        if hypothesis_id:
            node_id = f"hyp_{hypothesis_id}" if not hypothesis_id.startswith("hyp_") else hypothesis_id
            if self.graph.has_node(node_id):
                return node_id
        
        if hypothesis_text:
            for node_id, data in self.graph.nodes(data=True):
                if _is_node_type(data, NodeType.HYPOTHESIS):
                    if hypothesis_text.lower() in data.get("text", "").lower():
                        return node_id
        
        return None
    
    def _find_entity_nodes(
        self,
        entity_name: Optional[str],
        entity_id: Optional[str]
    ) -> List[str]:
        """Find entity nodes by name or ID"""
        nodes = []
        
        if entity_id:
            node_id = f"ent_{entity_id}" if not entity_id.startswith("ent_") else entity_id
            if self.graph.has_node(node_id):
                nodes.append(node_id)
        
        if entity_name:
            for node_id, data in self.graph.nodes(data=True):
                if _is_node_type(data, NodeType.ENTITY):
                    if entity_name.lower() in data.get("text", "").lower():
                        if node_id not in nodes:
                            nodes.append(node_id)
        
        return nodes
    
    def _find_claim_node(
        self,
        claim_id: Optional[str],
        claim_text: Optional[str]
    ) -> Optional[str]:
        """Find claim node by ID or text"""
        if claim_id:
            node_id = f"claim_{claim_id}" if not claim_id.startswith("claim_") else claim_id
            if self.graph.has_node(node_id):
                return node_id
        
        if claim_text:
            for node_id, data in self.graph.nodes(data=True):
                if data.get("node_type") == NodeType.CLAIM:
                    if claim_text.lower() in data.get("text", "").lower():
                        return node_id
        
        return None

"""Hypothesis inference engine - infer hypotheses from related claims"""

import os
import json
from typing import List, Dict, Any, Optional, Set
from openai import OpenAI
import networkx as nx
from ..graph.graph_schema import NodeType, EdgeType


class HypothesisInferencer:
    """Infer hypotheses from related claims across documents"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def infer_hypotheses(
        self,
        graph: nx.MultiDiGraph,
        min_supporting_claims: int = 2,
        max_hypotheses: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Infer new hypotheses from the graph structure
        
        Args:
            graph: The reasoning graph
            min_supporting_claims: Minimum number of claims needed to infer a hypothesis
            max_hypotheses: Maximum number of hypotheses to infer
        
        Returns:
            List of inferred hypotheses
        """
        # Find clusters of related claims
        claim_clusters = self._find_claim_clusters(graph, min_supporting_claims)
        
        inferred_hypotheses = []
        
        for cluster in claim_clusters[:max_hypotheses]:
            # Get claim texts
            claim_texts = []
            claim_ids = []
            
            for claim_node_id in cluster:
                node_data = graph.nodes[claim_node_id]
                if _is_node_type(node_data, NodeType.CLAIM):
                    claim_texts.append(node_data.get("text", ""))
                    claim_ids.append(claim_node_id)
            
            if len(claim_texts) < min_supporting_claims:
                continue
            
            # Infer hypothesis using LLM
            hypothesis = self._infer_from_claims(claim_texts, claim_ids)
            if hypothesis:
                inferred_hypotheses.append(hypothesis)
        
        return inferred_hypotheses
    
    def _find_claim_clusters(
        self,
        graph: nx.MultiDiGraph,
        min_size: int = 2
    ) -> List[List[str]]:
        """Find clusters of related claims"""
        clusters = []
        
        # Get all claim nodes
        claim_nodes = [
            node_id for node_id, data in graph.nodes(data=True)
            if _is_node_type(data, NodeType.CLAIM)
        ]
        
        # Group claims by shared entities
        entity_to_claims = {}
        for claim_node_id in claim_nodes:
            # Find entities connected to this claim
            connected_entities = []
            for neighbor in graph.neighbors(claim_node_id):
                if _is_node_type(graph.nodes[neighbor], NodeType.ENTITY):
                    connected_entities.append(neighbor)
            
            # Also check reverse (claims mentioning entities)
            for node_id, data in graph.nodes(data=True):
                if _is_node_type(data, NodeType.ENTITY):
                    if graph.has_edge(claim_node_id, node_id):
                        connected_entities.append(node_id)
            
            # Group by shared entities
            for ent_id in connected_entities:
                if ent_id not in entity_to_claims:
                    entity_to_claims[ent_id] = []
                entity_to_claims[ent_id].append(claim_node_id)
        
        # Find clusters with multiple claims
        seen_claims = set()
        for ent_id, claims in entity_to_claims.items():
            if len(claims) >= min_size:
                # Check if we've already seen this cluster
                claims_set = set(claims)
                if not any(claims_set.issubset(seen) for seen in seen_claims):
                    clusters.append(claims)
                    seen_claims.add(claims_set)
        
        # Also check for claims connected by EXTENDS edges
        for claim1 in claim_nodes:
            cluster = [claim1]
            for claim2 in claim_nodes:
                if claim1 == claim2:
                    continue
                # Check if there's an EXTENDS edge
                if graph.has_edge(claim2, claim1):
                    edge_data = graph.get_edge_data(claim2, claim1)
                    for edge_key, data in edge_data.items():
                        if data.get("edge_type") == EdgeType.EXTENDS.value:
                            cluster.append(claim2)
                            break
            
            if len(cluster) >= min_size:
                cluster_set = set(cluster)
                if not any(cluster_set.issubset(seen) for seen in seen_claims):
                    clusters.append(cluster)
                    seen_claims.add(cluster_set)
        
        return clusters
    
    def _infer_from_claims(
        self,
        claim_texts: List[str],
        claim_ids: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Use LLM to infer hypothesis from related claims"""
        claims_text = "\n\n".join([
            f"Claim {i+1}: {text}"
            for i, text in enumerate(claim_texts)
        ])
        
        prompt = f"""Given the following related scientific claims from different papers, infer the underlying shared hypothesis that these claims collectively support or test.

Claims:
{claims_text}

A hypothesis should be:
- A testable prediction or assumption
- More general than the individual claims
- Something that could explain or unify these claims

Return a JSON object with:
- "hypothesis": the inferred hypothesis text
- "confidence": confidence score (0.0-1.0)
- "reasoning": brief explanation of why this hypothesis was inferred

Return only valid JSON object."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a scientific reasoning expert. Infer hypotheses from related claims. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            data = json.loads(result)
            
            hypothesis_id = f"hyp_inferred_{hash(''.join(claim_ids)) % 10000}"
            
            return {
                "hypothesis_id": hypothesis_id,
                "text": data.get("hypothesis", ""),
                "supporting_claims": claim_ids,
                "confidence": float(data.get("confidence", 0.5)),
                "source": "inferred",
                "reasoning": data.get("reasoning", "")
            }
            
        except Exception as e:
            print(f"Error inferring hypothesis: {e}")
            return None
    
    def add_inferred_hypotheses_to_graph(
        self,
        graph: nx.MultiDiGraph,
        hypotheses: List[Dict[str, Any]]
    ) -> nx.MultiDiGraph:
        """Add inferred hypotheses to the graph"""
        for hyp in hypotheses:
            hyp_id = hyp.get("hypothesis_id", "")
            node_id = f"hyp_{hyp_id}"
            
            # Add hypothesis node
            graph.add_node(
                node_id,
                node_type=NodeType.HYPOTHESIS,
                text=hyp.get("text", ""),
                confidence=hyp.get("confidence", 0.5),
                source=hyp.get("source", "inferred"),
                reasoning=hyp.get("reasoning", "")
            )
            
            # Add edges from supporting claims
            supporting_claims = hyp.get("supporting_claims", [])
            for claim_id in supporting_claims:
                claim_node_id = f"claim_{claim_id}" if not claim_id.startswith("claim_") else claim_id
                if graph.has_node(claim_node_id):
                    graph.add_edge(
                        claim_node_id,
                        node_id,
                        edge_type=EdgeType.SUPPORTS.value,
                        weight=hyp.get("confidence", 0.5)
                    )
        
        return graph

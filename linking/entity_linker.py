"""Cross-document entity linking"""

from typing import List, Dict, Any, Set, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
from collections import defaultdict


class EntityLinker:
    """Link entities across documents"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize with embedding model"""
        self.model = SentenceTransformer(model_name)
        self.entity_embeddings: Dict[str, np.ndarray] = {}
        self.entity_clusters: Dict[str, List[str]] = defaultdict(list)
    
    def link_entities(self, entities: List[Dict[str, Any]], similarity_threshold: float = 0.75) -> Dict[str, List[str]]:
        """
        Link entities across documents
        
        Returns:
            Dictionary mapping canonical entity name to list of entity IDs
        """
        if not entities:
            return {}
        
        # Step 1: Compute embeddings for all entities
        entity_texts = [ent.get("text", "") for ent in entities]
        embeddings = self.model.encode(entity_texts, show_progress_bar=False)
        
        # Store embeddings
        for ent, emb in zip(entities, embeddings):
            ent_id = ent.get("entity_id", "")
            self.entity_embeddings[ent_id] = emb
        
        # Step 2: String-based exact and fuzzy matching
        string_links = self._string_based_linking(entities)
        
        # Step 3: Embedding-based similarity matching
        embedding_links = self._embedding_based_linking(
            entities, embeddings, similarity_threshold
        )
        
        # Step 4: Merge linkings
        merged_links = self._merge_linkings(string_links, embedding_links)
        
        return merged_links
    
    def _string_based_linking(self, entities: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Link entities based on string similarity"""
        links = defaultdict(list)
        processed = set()
        
        for i, ent1 in enumerate(entities):
            if ent1.get("entity_id") in processed:
                continue
            
            ent1_id = ent1.get("entity_id", "")
            ent1_text = ent1.get("text", "").lower().strip()
            ent1_type = ent1.get("entity_type", "")
            
            cluster = [ent1_id]
            processed.add(ent1_id)
            
            for j, ent2 in enumerate(entities[i+1:], start=i+1):
                ent2_id = ent2.get("entity_id", "")
                if ent2_id in processed:
                    continue
                
                ent2_text = ent2.get("text", "").lower().strip()
                ent2_type = ent2.get("entity_type", "")
                
                # Same type required
                if ent1_type != ent2_type:
                    continue
                
                # Exact match
                if ent1_text == ent2_text:
                    cluster.append(ent2_id)
                    processed.add(ent2_id)
                    continue
                
                # Fuzzy match (simple substring or abbreviation)
                if self._is_similar_string(ent1_text, ent2_text):
                    cluster.append(ent2_id)
                    processed.add(ent2_id)
            
            if cluster:
                # Use first entity as canonical
                canonical = entities[0].get("text", "") if i == 0 else ent1.get("text", "")
                links[canonical] = cluster
        
        return dict(links)
    
    def _is_similar_string(self, text1: str, text2: str) -> bool:
        """Check if two strings are similar (substring, abbreviation, etc.)"""
        # Exact match
        if text1 == text2:
            return True
        
        # One is substring of another
        if text1 in text2 or text2 in text1:
            return True
        
        # Abbreviation patterns (e.g., "BERT" vs "Bidirectional Encoder Representations from Transformers")
        # Simple check: if one is very short and contained in longer one
        if len(text1) <= 5 and len(text2) > 10:
            if text1.upper() in text2.upper():
                return True
        if len(text2) <= 5 and len(text1) > 10:
            if text2.upper() in text1.upper():
                return True
        
        # Word overlap (simple)
        words1 = set(text1.split())
        words2 = set(text2.split())
        if len(words1) > 0 and len(words2) > 0:
            overlap = len(words1 & words2) / max(len(words1), len(words2))
            if overlap > 0.6:
                return True
        
        return False
    
    def _embedding_based_linking(
        self, 
        entities: List[Dict[str, Any]], 
        embeddings: np.ndarray,
        threshold: float
    ) -> Dict[str, List[str]]:
        """Link entities based on embedding similarity"""
        links = defaultdict(list)
        processed = set()
        
        for i, ent1 in enumerate(entities):
            ent1_id = ent1.get("entity_id", "")
            if ent1_id in processed:
                continue
            
            ent1_type = ent1.get("entity_type", "")
            emb1 = embeddings[i]
            
            cluster = [ent1_id]
            processed.add(ent1_id)
            
            for j, ent2 in enumerate(entities[i+1:], start=i+1):
                ent2_id = ent2.get("entity_id", "")
                if ent2_id in processed:
                    continue
                
                ent2_type = ent2.get("entity_type", "")
                
                # Same type required
                if ent1_type != ent2_type:
                    continue
                
                emb2 = embeddings[j]
                
                # Compute cosine similarity
                similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                
                if similarity >= threshold:
                    cluster.append(ent2_id)
                    processed.add(ent2_id)
            
            if cluster:
                canonical = ent1.get("text", "")
                links[canonical] = cluster
        
        return dict(links)
    
    def _merge_linkings(
        self, 
        string_links: Dict[str, List[str]], 
        embedding_links: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """Merge string-based and embedding-based linkings"""
        merged = defaultdict(set)
        
        # Add string links
        for canonical, entity_ids in string_links.items():
            merged[canonical].update(entity_ids)
        
        # Add embedding links and merge clusters
        for canonical, entity_ids in embedding_links.items():
            # Check if any entity is already in a cluster
            found_cluster = None
            for existing_canonical, existing_ids in merged.items():
                if any(eid in existing_ids for eid in entity_ids):
                    found_cluster = existing_canonical
                    break
            
            if found_cluster:
                merged[found_cluster].update(entity_ids)
            else:
                merged[canonical].update(entity_ids)
        
        # Convert sets to lists
        return {canonical: list(entity_ids) for canonical, entity_ids in merged.items()}
    
    def get_linked_mentions(self, entity_name: str) -> List[str]:
        """Get all entity IDs linked to a canonical entity name"""
        return self.entity_clusters.get(entity_name, [])

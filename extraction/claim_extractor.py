"""Claim extraction from scientific documents"""

import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from openai import OpenAI


class Claim(BaseModel):
    """Represents an extracted claim"""
    claim_id: str
    text: str
    claim_type: str  # "comparative", "causal", "conclusive", "other"
    entities: List[str] = []  # Entity IDs or names mentioned
    doc_id: str
    sentence_id: str
    confidence: float = 0.5


class ClaimExtractor:
    """Extract claims from scientific text using LLM"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def extract_claims(self, sentences: List[Dict[str, Any]], entities: Optional[List[Dict[str, Any]]] = None) -> List[Claim]:
        """Extract claims from sentences"""
        all_claims = []
        
        # Create entity lookup
        entity_lookup = {}
        if entities:
            for ent in entities:
                entity_lookup[ent.get("text", "").lower()] = ent.get("entity_id", "")
        
        # Process in batches
        batch_size = 10
        for i in range(0, len(sentences), batch_size):
            batch = sentences[i:i+batch_size]
            batch_claims = self._extract_from_batch(batch, entity_lookup)
            all_claims.extend(batch_claims)
        
        return all_claims
    
    def _extract_from_batch(self, sentences: List[Dict[str, Any]], entity_lookup: Dict[str, str]) -> List[Claim]:
        """Extract claims from a batch of sentences"""
        text_batch = "\n\n".join([
            f"Sentence {idx}: {sent.get('text', '')}"
            for idx, sent in enumerate(sentences)
        ])
        
        prompt = f"""Identify scientific claims in the following sentences. A claim is a statement that:
- Makes a conclusion or assertion
- Compares methods/models/datasets
- States a causal relationship
- Presents experimental results

For each claim, identify:
1. The claim text (may be the full sentence or a part)
2. Claim type: one of ["comparative", "causal", "conclusive", "other"]
3. Entities mentioned (if any)
4. Confidence (0.0-1.0) that this is a significant claim

Return a JSON object with an "claims" array. Each claim should have:
- "text": the claim text
- "type": claim type
- "entities": list of entity names mentioned
- "sentence_idx": index in the batch (0-based)
- "confidence": confidence score

Sentences:
{text_batch}

Return only valid JSON object with "claims" array."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a scientific claim extraction expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            data = json.loads(result)
            claims_data = data.get("claims", [])
            
            # Convert to Claim objects
            claims = []
            for claim_data in claims_data:
                sentence_idx = claim_data.get("sentence_idx", 0)
                if sentence_idx < len(sentences):
                    sent = sentences[sentence_idx]
                    claim_id = f"{sent.get('sentence_id', '')}_claim_{len(claims)}"
                    
                    # Map entity names to IDs
                    entity_names = claim_data.get("entities", [])
                    entity_ids = [
                        entity_lookup.get(name.lower(), name)
                        for name in entity_names
                    ]
                    
                    claims.append(Claim(
                        claim_id=claim_id,
                        text=claim_data.get("text", ""),
                        claim_type=claim_data.get("type", "other"),
                        entities=entity_ids,
                        doc_id=sent.get("doc_id", ""),
                        sentence_id=sent.get("sentence_id", ""),
                        confidence=float(claim_data.get("confidence", 0.5))
                    ))
            
            return claims
            
        except Exception as e:
            print(f"Error extracting claims: {e}")
            return []
    
    def extract_from_sentence(self, sentence: Dict[str, Any], entities: Optional[List[Dict[str, Any]]] = None) -> List[Claim]:
        """Extract claims from a single sentence"""
        entity_lookup = {}
        if entities:
            for ent in entities:
                entity_lookup[ent.get("text", "").lower()] = ent.get("entity_id", "")
        return self._extract_from_batch([sentence], entity_lookup)

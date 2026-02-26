"""Hypothesis detection from scientific documents"""

import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from openai import OpenAI


class Hypothesis(BaseModel):
    """Represents a detected hypothesis"""
    hypothesis_id: str
    text: str
    doc_id: str
    supporting_claims: List[str] = []  # Claim IDs
    confidence: float = 0.5
    source: str = "explicit"  # "explicit" or "inferred"


class HypothesisDetector:
    """Detect explicit hypotheses from scientific text"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def detect_hypotheses(self, sentences: List[Dict[str, Any]], claims: Optional[List[Dict[str, Any]]] = None) -> List[Hypothesis]:
        """Detect explicit hypotheses from sentences"""
        all_hypotheses = []
        
        # Create claim lookup
        claim_lookup = {}
        if claims:
            for claim in claims:
                sent_id = claim.get("sentence_id", "")
                if sent_id not in claim_lookup:
                    claim_lookup[sent_id] = []
                claim_lookup[sent_id].append(claim.get("claim_id", ""))
        
        # Process in batches
        batch_size = 15
        for i in range(0, len(sentences), batch_size):
            batch = sentences[i:i+batch_size]
            batch_hypotheses = self._detect_from_batch(batch, claim_lookup)
            all_hypotheses.extend(batch_hypotheses)
        
        return all_hypotheses
    
    def _detect_from_batch(self, sentences: List[Dict[str, Any]], claim_lookup: Dict[str, List[str]]) -> List[Hypothesis]:
        """Detect hypotheses from a batch of sentences"""
        text_batch = "\n\n".join([
            f"Sentence {idx}: {sent.get('text', '')}"
            for idx, sent in enumerate(sentences)
        ])
        
        prompt = f"""Identify explicit scientific hypotheses in the following sentences. A hypothesis is:
- A testable prediction or assumption
- Often stated as "we hypothesize", "we propose", "we test whether"
- A statement about expected relationships or outcomes

For each hypothesis, identify:
1. The hypothesis text
2. The sentence index where it appears
3. Confidence (0.0-1.0) that this is a hypothesis

Return a JSON object with a "hypotheses" array. Each hypothesis should have:
- "text": the hypothesis text
- "sentence_idx": index in the batch (0-based)
- "confidence": confidence score

Sentences:
{text_batch}

Return only valid JSON object with "hypotheses" array."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a scientific hypothesis detection expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            data = json.loads(result)
            hypotheses_data = data.get("hypotheses", [])
            
            # Convert to Hypothesis objects
            hypotheses = []
            for hyp_data in hypotheses_data:
                sentence_idx = hyp_data.get("sentence_idx", 0)
                if sentence_idx < len(sentences):
                    sent = sentences[sentence_idx]
                    hyp_id = f"{sent.get('doc_id', '')}_hyp_{len(hypotheses)}"
                    
                    # Get supporting claims if any
                    supporting_claims = claim_lookup.get(sent.get("sentence_id", ""), [])
                    
                    hypotheses.append(Hypothesis(
                        hypothesis_id=hyp_id,
                        text=hyp_data.get("text", ""),
                        doc_id=sent.get("doc_id", ""),
                        supporting_claims=supporting_claims,
                        confidence=float(hyp_data.get("confidence", 0.5)),
                        source="explicit"
                    ))
            
            return hypotheses
            
        except Exception as e:
            print(f"Error detecting hypotheses: {e}")
            return []

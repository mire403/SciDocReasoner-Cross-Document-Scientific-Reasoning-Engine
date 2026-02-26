"""Entity extraction from scientific documents"""

import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from openai import OpenAI


class Entity(BaseModel):
    """Represents an extracted entity"""
    entity_id: str
    text: str
    entity_type: str  # "model", "method", "dataset", "metric", "biological", "chemical", "other"
    doc_id: str
    sentence_id: str
    context: str = ""


class EntityExtractor:
    """Extract entities from scientific text using LLM"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def extract_entities(self, sentences: List[Dict[str, Any]]) -> List[Entity]:
        """Extract entities from sentences"""
        all_entities = []
        
        # Process in batches to avoid token limits
        batch_size = 10
        for i in range(0, len(sentences), batch_size):
            batch = sentences[i:i+batch_size]
            batch_entities = self._extract_from_batch(batch)
            all_entities.extend(batch_entities)
        
        return all_entities
    
    def _extract_from_batch(self, sentences: List[Dict[str, Any]]) -> List[Entity]:
        """Extract entities from a batch of sentences"""
        # Prepare text for LLM
        text_batch = "\n\n".join([
            f"Sentence {idx}: {sent.get('text', '')}"
            for idx, sent in enumerate(sentences)
        ])
        
        prompt = f"""Extract scientific entities from the following sentences. For each entity, identify:
1. The entity name/text
2. Entity type: one of ["model", "method", "dataset", "metric", "biological", "chemical", "other"]
3. The sentence number where it appears

Return a JSON array of entities. Each entity should have:
- "text": the entity name
- "type": entity type
- "sentence_idx": index in the batch (0-based)

Sentences:
{text_batch}

Return only valid JSON array, no other text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a scientific entity extraction expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = response.choices[0].message.content
            # Try to extract JSON array
            import json
            # Handle both array and object responses
            try:
                data = json.loads(result)
                if isinstance(data, dict) and "entities" in data:
                    entities_data = data["entities"]
                elif isinstance(data, list):
                    entities_data = data
                else:
                    entities_data = []
            except:
                entities_data = []
            
            # Convert to Entity objects
            entities = []
            for ent_data in entities_data:
                sentence_idx = ent_data.get("sentence_idx", 0)
                if sentence_idx < len(sentences):
                    sent = sentences[sentence_idx]
                    entity_id = f"{sent.get('sentence_id', '')}_ent_{len(entities)}"
                    entities.append(Entity(
                        entity_id=entity_id,
                        text=ent_data.get("text", ""),
                        entity_type=ent_data.get("type", "other"),
                        doc_id=sent.get("doc_id", ""),
                        sentence_id=sent.get("sentence_id", ""),
                        context=sent.get("text", "")
                    ))
            
            return entities
            
        except Exception as e:
            print(f"Error extracting entities: {e}")
            return []
    
    def extract_from_sentence(self, sentence: Dict[str, Any]) -> List[Entity]:
        """Extract entities from a single sentence"""
        return self._extract_from_batch([sentence])
